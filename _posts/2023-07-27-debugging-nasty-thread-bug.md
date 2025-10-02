# Debugging a nasty thread bug

Some years ago I worked on a GUI project, which needs to 
stream video on screen, while paint some UI over video layer.
Our Project Manager decided to port this from ARM to X86.
The challenge is how to make this UI painting portable while still performant.

To achieve reasonable FPS on current low-profile ARM device,
previous implementation use device specified API to drive the display controller directly, 
you can blit pixels directly into display controller baking buffer,
which will be flushed on screen without passing through normal OS screen buffer.
It also supports 'color key', when you paint GUI interface over
that special buffer layer, display controller will make any 
pixels with the color key to transparent, 
allow the application draw toolkit over underlay video layer.

We decide to migrate this to OpenGL shader based approach, 
first reason is that another production line already using shader based image processing algorithm,
we hope to reuse that work, another reason is that we're using Qt toolkits,
its QtGraphicScene component can be configured to use shared context, 
thus making image processing and toolkit painting in same context.


To ease that migration, we also consider using gstreamer pipeline, 
It's designed for video playback, portable/performant/easy-to-use,
supports OpenGL display, also have a Qt shared context example, seems quite a good fit.
But actually it has many hidden problems in practise,
If we reconsider the decision from the present point of view, gstreamer is still involving quickly during that time (
it's still 0.1x version when our project start),
and it's very risky to use that in a production. It takes
me about half a year to complete the migration, half of the time I'm digging
into gstreamer to point out how to make it work to satisfy our usage, later
I spend more time to keep API compatible with newer version,
and keep finding new bugs. 


But such development process is a very interesting journey to me, Since I have to learn how
it works and tell whether the problem is from my code or from gstreamer itself,
I had to ask developers a lot by mail listing, and I learn
how open source software being developed, how its community running, and how
to contribute back to it. This makes me fall in love with open source.

First problem I've faced is how to feed video data into its pipeline by loading from memory.
Video loading from file is reliable but not for loading through API at that time, especially input format/size can be dynamic changed.
Thus this is my [life-first open source patch submission](https://bugzilla.gnome.org/show_bug.cgi?id=729760),
I only report the issue to mail listing, patch is mostly based on 
suggestions of gstreamer's developers.


And later on, I mostly worked on the OpenGL stuff, find/fix random bugs
with help from developers (especially Matthew Waters (ystreet00)/
Sebastian Dröge (slomo)/Tim-Philipp Müller/ and many among others), like
use-after-free/[race-condition](https://bugzilla.gnome.org/show_bug.cgi?id=734830)
and other misc ones. To makes our project running 
without problem, I've also submitted a simple (yet useful enough)
[leak tracing](https://github.com/apitrace/apitrace/issues/416) 
function to API trace (final python implementation written by author
instead of my C++ one), with this tool, many object leak bugs also being addressed,
makes gstreamer and our project more and more stable.


I also spend lots of time on OpenGL context sharing, to improve gstreamer general stability.
I found some strange bugs in our project and gstreamer,
which lead by OpenGL context sharing dirty tricks, 
different vendor/driver/OS behavior, but finally I fix all of them, 
our Application has stable context sharing under Linux/Windows AMD/Nvidia, only with one exception: 
While running on windows XP, it randomly stop streaming images, with one gstreamer 
thread deadloop. after days and days repeating debugging, I realized that
it must have a low-level threading logic bug, from gthread (a library that Gstreamer used as portable pthread implementation) itself.
otherwise g_cond_broadcast (pthread_broadcast equivalent) shouldn't dead looping.
I never think about this possibility since it's being used as the thread implementation
by all GTK application on Windows XP, if there's bug in it,
it should be spot by others as well, But the truth is that
other application do suffer from similar issue (I think DIA, a diagram editor also random dead on windows XP)
just not that many people care about it, seems I'm the first one whom need to fix it badly.
Now let's dig into the rabbit hole.

The Gstreamer threading model at high level looks like this: (IIRC)

  1. OpenGL has implicit thread local context bind,
     A GL control thread is used to call all OpenGL functions, that thread own the OpenGL context,
     its only responsible is to run callbacks from sending thread.

  2. Other thread can inject a callback using something like 
     ```call_on_gl_thread```, to inject callback into control thread slot,
     that callback will be run on the control thread, so it's safe to call OpenGL functions there.
     call_on_gl_thread also only return after the callback complete from control thread.

  3. OpenGL control thread must wait other thread complete inserting callback 
     for every paint loop, so there will be a condvar , which sending thread tell
     OpenGL control thread it complete inserting the callback.

  4. after OpenGL Control thread got the callback, it runs that callback, and use another condvar 
     to tell sending thread that callback already complete.

  5. next loop

To hunt the bug, I've inserted bunch of assert/logs in gthread, then run my testcase over and over,
to understand its behavior, expect any assert violating tells me the inconsistencies.
Since this bug might due to incorrect threading implementation ( for example some thread primitive 
not work as expected), these assert might also give false positive. With days and days testing,
I slowly got the idea on how gthread emulate pthread under windows.

gthread mimic pthread with minor naming change, It compile to exactly same pthread stubs under linux,
on Windows >= Vista, it's implementation is to emulate pthread with Vista API,
on windows XP, they first emulate the Vista API, then use the Vista based implementation.

Let's paste some code, the wait part(g_cond_wait):
```C
static BOOL __stdcall
g_thread_xp_SleepConditionVariableSRW (gpointer cond,
                                       gpointer mutex,
                                       DWORD    timeout,
                                       ULONG    flags)
{
  GThreadXpCONDITION_VARIABLE *cv = g_thread_xp_get_condition_variable (cond);
  GThreadXpWaiter *waiter = g_thread_xp_waiter_get ();
  DWORD status;

  waiter->next = NULL;

  EnterCriticalSection (&g_thread_xp_lock);
  waiter->my_owner = cv->last_ptr;
  *cv->last_ptr = waiter;
  cv->last_ptr = &waiter->next;
  LeaveCriticalSection (&g_thread_xp_lock);

  g_mutex_unlock (mutex);
  status = WaitForSingleObject (waiter->event, timeout);

  if (status != WAIT_TIMEOUT && status != WAIT_OBJECT_0)
    g_thread_abort (GetLastError (), "WaitForSingleObject");
  g_mutex_lock (mutex);

  if (status == WAIT_TIMEOUT)
    {
      EnterCriticalSection (&g_thread_xp_lock);
      if (waiter->my_owner)
        {
          if (waiter->next)
            waiter->next->my_owner = waiter->my_owner;
          else
            cv->last_ptr = waiter->my_owner;
          *waiter->my_owner = waiter->next;
          waiter->my_owner = NULL;
        }
      LeaveCriticalSection (&g_thread_xp_lock);
    }

  return status == WAIT_OBJECT_0;
}


```

wake all (g_cond_broadcast):
```C
static void __stdcall
g_thread_xp_WakeAllConditionVariable (gpointer cond)
{
  GThreadXpCONDITION_VARIABLE *cv = g_thread_xp_get_condition_variable (cond);
  volatile GThreadXpWaiter *waiter;

  EnterCriticalSection (&g_thread_xp_lock);

  waiter = cv->first;
  cv->first = NULL;
  cv->last_ptr = &cv->first;

  while (waiter != NULL)
    {
      volatile GThreadXpWaiter *next;

      next = waiter->next;
      SetEvent (waiter->event);
      waiter->my_owner = NULL;
      waiter = next;
    }

  LeaveCriticalSection (&g_thread_xp_lock);
}
```


and the wake one(g_cond_signal):
```C
static void __stdcall
g_thread_xp_WakeConditionVariable (gpointer cond)
{
  GThreadXpCONDITION_VARIABLE *cv = g_thread_xp_get_condition_variable (cond);
  volatile GThreadXpWaiter *waiter;

  EnterCriticalSection (&g_thread_xp_lock);

  waiter = cv->first;
  if (waiter != NULL)
    {
      waiter->my_owner = NULL;
      cv->first = waiter->next;
      if (cv->first != NULL)
        cv->first->my_owner = &cv->first;
      else
        cv->last_ptr = &cv->first;
    }

  if (waiter != NULL)
    SetEvent (waiter->event);

  LeaveCriticalSection (&g_thread_xp_lock);
}

```

and underlay win32 Event creation:
```C
static GThreadXpWaiter *
g_thread_xp_waiter_get (void)
{
  GThreadXpWaiter *waiter;

  waiter = TlsGetValue (g_thread_xp_waiter_tls);

  if G_UNLIKELY (waiter == NULL)
    {
      waiter = malloc (sizeof (GThreadXpWaiter));
      if (waiter == NULL)
        g_thread_abort (GetLastError (), "malloc");
      waiter->event = CreateEvent (0, FALSE, FALSE, NULL);
      if (waiter->event == NULL)
        g_thread_abort (GetLastError (), "CreateEvent");
      waiter->my_owner = NULL;

      TlsSetValue (g_thread_xp_waiter_tls, waiter);
    }

  return waiter;
}
```

simply put:

1. use CriticalSection as mutex
2. use win32 Event to emulate condition variable blocking/waking
3. when g_cond_wait being called, gthread create a TLS structure (waiter), which contains one win32 Event.
4. it append this waiter to corresponding condvar waiter list, then call WaitForSingleObject to enter that thread into sleep state
5. g_cond_boardcast being called on other thread, it finds the event from waiter list, calling SetEvent to wake wait thread, also remove that waiter from waiter list so it won't be wake again
6. the wait thread return from WaitForSingleObject, check return value to know if it's being waked, or timeout
7. if WaitForSingleObject timeout, it remove waiter from condvar waiter list, so it won't be wake again



Such logic seems correct at first glance, I know there must be some issues in it,
so I monitor these state while repeat running our application, then I discovered that
if the application has more than one thread calling `call_on_gl_thread`, sometimes
even before sending thread calling g_cond_boardcast, 
the control thread just returning from g_cond_wait, like being waked ? 
then I replay these steps in my mind, finally found the issue. Let me highlight the buggy part
with pseudo code.

```C
static void __stdcall
g_thread_xp_WakeConditionVariable (gpointer cond)
{
  ...
  EnterCriticalSection (&g_thread_xp_lock);
  if (has_one_waiter){
    remove it from waiter list
    SetEvent (waiter->event); 
  LeaveCriticalSection (&g_thread_xp_lock);
}
```

```C
static BOOL __stdcall
g_thread_xp_SleepConditionVariableSRW (gpointer cond,
                                       gpointer mutex,
                                       DWORD    timeout,
                                       ULONG    flags)
{
  ...

  EnterCriticalSection (&g_thread_xp_lock);

  append this waiter to condvar waiter list

  LeaveCriticalSection (&g_thread_xp_lock);

  g_mutex_unlock (mutex);
  status = WaitForSingleObject (waiter->event, timeout);
  ...
  g_mutex_lock (mutex);

  if (WaitForSingleObject_return_timeout)
    {
      EnterCriticalSection (&g_thread_xp_lock);
      if (this_still_in_condvar_waiter_list)
        {
          remove_this_from_condvar_waiter_list
        }
      LeaveCriticalSection (&g_thread_xp_lock);
    }

  return status == WAIT_OBJECT_0;
}
```

Did you see the issue? on the wait thread, there will only be one Win32 Event for sleep/wake,
since it can't be more than one Event entering sleeping state in one thread at same time right?
so that Event is reused by different condvar. condvar use waiter list for that ownership bookmark.
The manipulation might happen in either wake thread or wait thread,
gthread use g_thread_xp_lock CriticalSection to avoid race, but there's a hole:
if wait thread already returned from WaitForSingleObject with TIMEOUT,
then wake thread call SetEvent after that, the Event will have a pending
signaled state, this might not be an issue for this condvar,
but this staled state lead next WaitForSingleObject return immediately,
even wait thread calling g_cond_wait on a different condvar B. 
then wait thread thinks it's being waken up and expect the bookmark already taken place by that wakeup step
(which is actually from previous different condvar wake)
it then takes none-timeout branch and skip ownership manipulating,
leave the waiter in condvar waiter list, then thread wait on condvar B again,
it add same waiter to waiter list, makes that link list a self cycle.
Thus g_cond_broadcast (it walk link list to wakeup all Event) will deadloop.


To summarize:


1. It's impossible to let WaitForSingleObject being under mutex protection (otherwise it won't release the mutex during sleep)
2. There will be window that win32 Event have pending signaled state, this can't be tell only from WaitForSingleObject return value (since it already returned), then such signaled state leaked from the ownership bookmarking
3. Such leakage confusing following bookmarking, leads the self cycle deadloop.


Problem 1 is unresolvable, let's see if 2/3 can be fixed. Partially problem 2 is due to the manipulation
not keep sync with the win32 Event, we can always updating ownership, not only when timeout. So no matter
if we're waken by TIMEOUT or WAIT_OBJECT_0, we always clean self from waiter list, then even there's pending
state in Win32 Event, waiter entry always being removed from waiter linked list, thus avoid the deadloop.
by definition condition variable is allowed to have 'spurious wakeup', even such staled state
leads wake up of wrong condition variable, it's still 'correct' 
(that's the reason why condition variable must always being used with another variable check,also within loop).
so strictly speaking Problem 3 is not an issue, as long as there's no self cycle deadloop. 
My patch also improve Problem 3 by introducing the hash table, every condition variable have their own Event, the spurious wakeup
can still happen, but only on same condition variable (if we don't want to create new Event everytime call g_cond_wait)

Another possible fix could be calling ResetEvent as last step of ownership manipulation (also under protection of g_thread_xp_lock), then staled state won't leak to next WaitForSingleObject call. This approach has a misc drawback:
all pending condition variable wake will be lost everytime after g_cond_wait return. That might not be a big issue since
current implementation also lose all pending wakeup before first g_cond_wait (win32 Event only created at first g_cond_wait).

the full discussion and patch here:
https://bugzilla.gnome.org/show_bug.cgi?id=762853

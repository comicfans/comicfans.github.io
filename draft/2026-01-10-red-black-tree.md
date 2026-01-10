# Red-Black tree, in English


People say that "If I can't coding it, then I don't understand it", so I spend some days to implement the red-black tree. 
Most people feel confusing when learning the rules of RB-tree insertion and deletion just like me, so I want to clear these confusion in this blog.
I read several blog , also asking chatgpt to explain some details, but found implementing it myself is still the best way to understand it.
(Note: this blog only cover the unique-value implementation like std::set, but the basic idea still stay the same for std::multiset)

Before entering RB-tree, let's revise binary search tree (BST) first, some confusion explain in RB-tree actually came from the convention in BST
the property of binary search tree:

1. parent node value is greater than any node of left-child sub-tree, and less than any node of right-child sub-tree
2. the in-order successor element of a node, is the left-most node of right-child sub-tree, in-order predecessor is the right-most node of left-child sub-tree
3. new inserted node (if it's not duplicated), will always insert as leaf node, say, replace a null child, it will never 'replace' any existing node, or as the third child of some node
4. most important rule (to help understanding RB-tree deletion): when remove a value, we never remove the node directly, we always swap it with in-order successor (or predecessor), then we remove the replaced node

rule4 is important for BST deletion: when the node you want to delete has two children (and corresponding sub-tree), you don't need to reconstruct whole structure
under the deletion node, instead , the problem turned into a left-most(or right-most) node deletion.  Since it's left-most (or right-most) node, so either it has no children at all, which is a leaf node that can be deleted directly, or has only one child, then such child can be directly attached to parent node of deletion node. Consider following
condition:

graph


because the deletion node is left-most node of right-child sub-tree (if it's right-most then everything mirrored), it can only contain right-child, and according to rule1, this sub-tree is all less than parent node, so after deletion, it can be directly attached to parent left-node (to replace the deletion node)

Now let's get into RB-tree. Lots of post explain RB-tree by it's definition and operation rule first, I found myself better understand it by combine the rule and corresponding goal of the rule together, so I explain RB-tree rules as goal-first rules (please note, these rules differs to the ones listed by other reference):

1 why mark node with Red/Black color?  by combining color rules, this help BST avoiding decay to linear list
2 how to avoid BST decay to linear list?  by enforcing longest path won't be longer than 2 times of shortest path
3 how to enforce longest path shorter than 2 times of shortest path? Suppose that we have one such tree, then:
      let path node difference (D) between longest (L) and shortest (S) path, will be shorter than shortest path, say
      L <= S + S
      S <= L / 2
      D = L - S 
      D <= S
      so we can simply treat D as the number of red nodes, S as the number of black nodes
      because D < S, so we can always spread red nodes in-between the black nodes, without any two red-nodes stay in row
      only if longest path extend to its maximum value S*2 , we need so many red nodes ( D = S ), other than that, we can
      have much fewer red nodes
4 to ease the formula, we requires that root node are always black, since it's always the shared part of longest and shortest path,
  set it to black won't affect the D (which must be red)
5 to make logic more consist, we treat all empty nodes as black as well, so we have
  L < S + S
  D < S
  S < L / 2

then we revise the rule of red coloring:
red-node can't be consequent : red-node is to help filling the differences between longest and shortest path, as we keep it non-consequent,
it won't be more than half of the longest path, so L < S * 2

6 every path have exactly same black height  (same black node number)

(Please note: these rules are 'inversion explanation', just to help understanding the rules, not the mathematical prove. 
Some properties such as 6, and the insertion/deletion actually came from 2-3-4 tree, 
but this blog try to explain RBTree from BST perspective)

according to black height definition, we know that:

property 1 : RED node doesn't contribute to black height

property 2 : if we have two nodes, then parent must be Black, and child must be RED (otherwise the black height won't be equal)

property 3:  if we have three nodes (as subtree), it can only be 

    R            B
   /  \         / \
   B  B        R   R

   since any other structure violate RB-Tree rules
                       
                       
property 4:  all path black height equal, since two child sub-tree share same root path,
             their sub-tree black height are also equal

property 5: turn RED-NODE to BLACK won't lead consequent RED, only BLACK->RED can


so we'd better keep two ideas simultaneously, one set is the rule of RB-Tree, another is the goal of the rules.

then we apply similar idea to RBT insertion: we begin with an valid RB-Tree, 
inserting new node as BST : always insert as leaf, then try minimum steps to fix any violation, to make it an valid RB-Tree again. we try to fix it locally, only recursively back along parent if local fix impossible.  what does "local fix" mean ? If after applying some options (change structure or recoloring),  the black height is same (as before insertion) from higher level's perspective, then we already fixed it, it means we have some sparse room, to fill new nodes (either directly or indirectly into RED-position) without increasing longest height path.


1. treat new Node as RED. why RED ? because RED doesn't contribute to black height, so it's possible to only fix violation locally,
   or just along current path (as we can see later). But if insert as BLACK, it immediately increase black height by 1, since all path have exactly same black height
   that will requires violation fixing cascaded on all paths, which is sub-optimal.

2. if the parent is BLACK, then we already done (property 1) 
   graph

3. if the parent is RED,  then it must contains no children before insertion (othwerwise violate property 2),
   and since root is always black ,so parent is also not root, so possible structure is (position can be left or right, doesn't matter)
            G(grandparent)=BLACK                  grandparent must be black (because parent is already RED)
            /              \
         P(arent)=RED       U(ncle)            uncle might not exist, if exist, then must be RED
         /
      N(ew)=RED

most people (including me) feels confusing at these cases testing at first time due to the 'rotation', I try to avoid this term first, just remember our goal: try minimal steps to fix the 
violation locally

3.1  if uncle not exist, then we simply turn G/P/N to balanced structure , so black height not changed
     and everything done. Why color it as BLACK-RED-RED,  not RED-BLACK-BLACK ? both coloring won't change black height, but RED-BLACK-BLACK might lead consequent red (with grandgrandparent), which requires recursively fixing, is sub-optimal.

     graph
     
3.2 if uncle exist, then it must be RED. for such situation, we color Grandparent as red, P/U as BLACK (so the black height), then sub-tree under grandparent is fixed, but if grandgrandparent is red
we need recusively fix it.  An important point is that grandparent rooted sub-tree is balanced and black height equals to before insertion, which means if all step of recursive preserve these two properties, and not introduce new potential violation, we already fix the whole tree.


4 let's consider if this is possible: this action will turn a BLACK-RED-RED structure to  RED-BLACK-BLACK structure, such conversion won't change black height, just move down the parent black into two children root. consider property 5, this action never break uncle tree, and same as 3.2, it will make grandparent rebalanced (also black height not change), only potentially break consequent red rule, when recursive reach any black node (ROOT is always black), then everything is fine there.


Where is the 'rotation' ?
actually I think it's more implementation detail than helping understanding rebalance.
consider we have following BST structure, and want to turn it into 
      (G)B            (P)B 
      /               /  \
    (P)R   =>     (N)R   (G)R
   /
 (N)R

because of BST nature, you can wrote the code to 'right rotate' to make left structure into right one.
I find the plot much easier to understand without 'rotation' term.


then deletion: deletion is more complex, but basic idea stay the same :make minimum steps to fix the violation, 
try locally first. 
and important point: we're not deleting target node directly, we always delete 
the switched in-order successor as BST, so that node is always a leaf node, or 
a black node with only one right-red child. This makes it much easier to understand
(depends on target node position, you can also apply special operation directly without
swapping, but my implementation always do swapping first
without goto which I think is clear)

so our deletion steps: 

1. always swap 




I didn't including my implementation code here since it's not the best, I hope readers not being misguided by my sub-optimal code,
and I encourage readers to understand the idea of every action, then implement it theirselves. Personally I can't 
write a correct implementation without understanding the basic idea of RB-Tree, neither did I can fully understand the details 
without finish (and fixing) the implementation.

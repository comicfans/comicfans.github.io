from bst import TreeNode,Dir,BST,BSTAnimationCallback,AnimationCallback
import pdb
import copy
import random
from enum import Enum
from typing import Tuple
import manim
from manim import Animation,Scene

class Color(Enum):
    BLACK = 0
    RED = 1

class RBNode(TreeNode):
    def __init__(self,value):
        super().__init__(value)
        self.color_ = Color.RED

    def swap(self, to_swap):
        super().swap(to_swap)
        self.color_, to_swap.color_ = to_swap.color_, self.color_

    def __repr__(self):
        return super().__repr__() + str(self.color_)

class RBTreeAnimationCallback(BSTAnimationCallback):
    def on_new_tree_node(self, tree_node):
        super().on_new_tree_node(tree_node)
        self.node_for(tree_node).circle.set_color(manim.RED)

    def position_nodes(self, tree):
        super().position_nodes(tree)

        animation = []
        def rec_color(tree_node):
            if not tree_node:
                return

            call_obj = self.node_for(tree_node).circle
            if self.enabled:
                call_obj = call_obj.animate

            ani = call_obj.set_color(manim.RED if tree_node.color_ == Color.RED else manim.DARK_GRAY)
            if self.enabled:
                animation.append(ani)
            rec_color(tree_node.children_[Dir.LEFT.value])
            rec_color(tree_node.children_[Dir.RIGHT.value])

        rec_color(tree.root)
        self.flush_animation(animation)


    

class RBTree(BST):

    def new_node(self, value)->RBNode:
        return RBNode(value)

    def remove_fix(self, lowest_node, lowest_dir)->Tuple[RBNode, Dir]:
        if lowest_node == self.root:
            return [None,None]

        assert lowest_node.color_ == Color.BLACK

        parent = lowest_node.parent_
        assert parent

        sibling = parent.children_[1 - lowest_dir.value]
        # we're dealing with black height decrease1, so sibling branch always 
        # have at least one black node (that is , sibling must exist)
        assert sibling


        near_nephew = sibling.children_[lowest_dir.value]
        far_nephew = sibling.children_[1-lowest_dir.value]

        near_nephew_red = near_nephew and near_nephew.color_ == Color.RED
        far_nephew_red = far_nephew and far_nephew.color_ == Color.RED

        if near_nephew_red or far_nephew_red:
            # at least one nephew is red, or both red

            assert sibling.color_ == Color.BLACK
            if not far_nephew_red:
                new_sibling = self.rotate(sibling, Dir(1 - lowest_dir.value))
                new_sibling.color_ = Color.BLACK
                sibling.color_ = Color.RED
                sibling = new_sibling

            new_parent = self.rotate(parent, lowest_dir) # new parent is old sibling
            new_parent.color_ = parent.color_
            parent.color_ = Color.BLACK
            if new_parent.children_[1 - lowest_dir.value]:
                new_parent.children_[1 - lowest_dir.value].color_ = Color.BLACK

            return [None,None]
            

        #both nephews are black

        if parent.color_ == Color.RED:
            assert sibling.color_ == Color.BLACK
            # using parent red to rebalance

            parent.color_ = Color.BLACK
            # this is safe since both nephews are black
            sibling.color_ = Color.RED
            return [None,None]

        assert parent.color_ == Color.BLACK
        # and both nephews are black

        if sibling.color_ == Color.RED:
            # use sibling red to rebalance
            self.rotate(parent, lowest_dir)
            sibling.color_, parent.color_ = parent.color_, sibling.color_
            # it will turn into existing situation
            return [lowest_node, lowest_dir]


        #sibling, parent, nephew all black, push black height-1 upwards
        sibling.color_ = Color.RED

        grandparent = parent.parent_
        parent_dir = Dir(grandparent.children_[Dir.RIGHT.value] == parent) if grandparent else None
        return parent, parent_dir


    def remove(self, value)->Tuple[TreeNode, Dir]:
        to_delete_node, self_dir = super().remove(value)


        if self.root is None or self_dir is None:
            # clear tree or node is root to remove
            self.check(True,True)
            return [to_delete_node,self_dir]

        if to_delete_node.color_ == Color.RED:
            self.check(True,True)
            return [to_delete_node,self_dir]

        assert to_delete_node.color_ == Color.BLACK
        # deleting black, find if we can use sparse red node to complete it
       
        # here we're first iteration
        if to_delete_node.children_[Dir.RIGHT.value]:
            # the only condition that we might use child red to rebalance
            assert to_delete_node.children_[Dir.RIGHT.value].color_ == Color.RED
            to_delete_node.children_[Dir.RIGHT.value].color_ = Color.BLACK
            self.animation_callback.position_nodes(self)
            self.check(True,True)
            return True

        lowest_node = to_delete_node
        while lowest_node:
            lowest_node, lowest_dir  = self.remove_fix(lowest_node, self_dir)
            self_dir = lowest_dir

            self.check()
            self.animation_callback.position_nodes(self)

        self.animation_callback.position_nodes(self)
        self.check(True,True)
        return True

    def insert_fix(self, new_node)->RBNode:
        assert new_node.color_ == Color.RED

        if new_node == self.root:
            return None

        parent = new_node.parent_
        assert parent

        if parent.color_ == Color.BLACK:
            return None

        if parent == self.root:
            parent.color_ = Color.BLACK
            return None
        # double red and have grandparent
        grandparent = parent.parent_
        assert grandparent
        #assert grandparent.color_ is Color.BLACK

        parent_dir = Dir(int(parent == grandparent.children_[Dir.RIGHT.value]))
        uncle = grandparent.children_[1 - parent_dir.value]
        self_dir = Dir(int(new_node == parent.children_[Dir.RIGHT.value]))

        grandparent_is_root = grandparent == self.root
        if not uncle:
            #      B              B
            #     /              /
            #    R       or     R    for this , first rotate at parent to parent dir, then it becomes 1
            #   /                \
            #  R                  R
            #   
            #
            #                        B
            #   all became         /   \
            #                     R     R
            if self_dir != parent_dir:
                self.rotate(parent, parent_dir)


            new_sub_root = self.rotate(grandparent, Dir(1 - parent_dir.value))
            # recolor G and P
            grandparent.color_ = Color.RED
            new_sub_root.color_ = Color.BLACK

            if grandparent_is_root:
                self.root = new_sub_root

            return None

        # has uncle
        if uncle.color_ == Color.BLACK:
            #    G(B)                P(B)
            #   /    \               /   \
            #  P(R)   U(B)   =>    L(R)  G(R)
            #  /  \    /  \               /   \
            #L(R) S(B) .  .. ..         S(B)   U(B)

            #
            #    G(B)                      G(B)
            #   /    \                     /  \
            #  P(R)   U(B)   =>          L(R) U(B)  (then becomes first situation)
            #  /  \    /  \              /
            #S(B) L(R) .  .. ..        P(R)
            #                          /
            #                        S(B)

            if self_dir != parent_dir:
                self.rotate(parent, parent_dir) 


            new_sub_root = self.rotate(grandparent,Dir(1 - parent_dir.value))
            new_sub_root.color_ = Color.BLACK
            grandparent.color_ = Color.RED

            return None
        # uncle is red
        #             G(B)
        #            /   \
        #          P(R)   U(R)
        #          /
        #        L(R)
        #
        #
        grandparent.color_ = Color.RED
        parent.color_ = Color.BLACK
        uncle.color_ = Color.BLACK
        return grandparent

    def insert(self, value)->bool:

        to_fix_node = super().insert(value)

        if not to_fix_node:
            return None


        while to_fix_node:
            to_fix_node = self.insert_fix(to_fix_node)
            self.animation_callback.position_nodes(self)

        self.check(True)

        return to_fix_node

    def check(self, check_color= False, check_height = False):
        super().check()
        
        def do_check(root_node):

            if not root_node:
                return 0

            black_height = [0,0]

            for dir in Dir:
                child = root_node.children_[dir.value]
                if not child:
                    continue

                assert root_node == child.parent_
                if check_color:
                    #assert True
                    assert not (root_node.color_  == Color.RED and child.color_ == Color.RED)
                black_height[dir.value] = do_check(child)

            if check_height:
                assert black_height[0] == black_height[1]
            return black_height[0] + int(root_node.color_ == Color.BLACK)

        do_check(self.root)



class RbtInsert1(Scene):
    def construct(self):
        callback = RBTreeAnimationCallback(self)
        callback = AnimationCallback()
        rbt = RBTree(callback)

        #rand_data = [0,5,3]
        rand_data = list(range(20))
        random.seed(0)
        random.shuffle(rand_data)
        for i in rand_data:
            rbt.insert(i)

        random.shuffle(rand_data)
        for i in rand_data:
            print(i)
            rbt.remove(i)

        #rand_data = list(range(20))
        #random.shuffle(rand_data)
        #for i in rand_data:
        #    rbt.insert(i)
        #self.wait(1)

def test_case0():
    input = [10, 18, 16, 14, 0, 17, 11, 2, 3, 9]

    callback = AnimationCallback()
    rbt = RBTree(callback)
    for i in input:
        rbt.insert(i)

def test_case1():
    rand_data = list(range(1000))
    callback = AnimationCallback()
    rbt = RBTree(callback)

    random.seed(0)
    for j in range(1000):
        random.shuffle(rand_data)
        for i in rand_data:
            rbt.insert(i)

        copy_remove = copy.deepcopy(rand_data)
        random.shuffle(copy_remove)
        for i in copy_remove:
            rbt.remove(i)
        assert rbt.root is None

def test_case2():

    rand_data = [1, 7, 6, 2, 5, 4, 9, 3, 8, 0]
    callback = AnimationCallback()
    rbt = RBTree(callback)
    for i in rand_data:
        rbt.insert(i)

    for i in [8, 6, 9, 5, 7, 1, 3, 0, 2, 4]:
        rbt.remove(i)

    assert rbt.root is None

def test_case3():

    rand_data = [2, 4, 0, 3, 1]
    callback = AnimationCallback()
    rbt = RBTree(callback)
    for i in rand_data:
        rbt.insert(i)

    for i in [4, 3, 1, 2, 0]:
        if i == 2:
            pdb.set_trace()
        rbt.remove(i)

    assert rbt.root is None



#test_case1()

class RbtInsertNoUncle(Scene):
    def construct(self):
        callback = RBTreeAnimationCallback(self)
        callback.enabled = False
        rbt = RBTree(callback)

        for i in [5,3]:
            rbt.insert(i)
        callback.position_nodes(rbt)
        callback.enabled = True
        callback.position_nodes(rbt)
        rbt.insert(1)
        self.wait(1)


class RbtInsertNoUncle2(Scene):
    def construct(self):
        callback = RBTreeAnimationCallback(self)
        callback.enabled = False
        rbt = RBTree(callback)

        for i in [5,3]:
            rbt.insert(i)
        callback.position_nodes(rbt)
        callback.enabled = True
        callback.position_nodes(rbt)
        rbt.insert(4)
        self.wait(1)
        

class RbtInsertRedUncle(Scene):
    def construct(self):
        callback = RBTreeAnimationCallback(self)
        callback.enabled = False
        rbt = RBTree(callback)

        for i in [3,2,4]:
            rbt.insert(i)
        callback.position_nodes(rbt)
        callback.enabled = True
        callback.position_nodes(rbt)
        rbt.insert(1)
        self.wait(1)
        



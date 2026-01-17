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

class RBTreeAnimationCallback(BSTAnimationCallback):
    def on_new_tree_node(self, tree_node):
        super().on_new_tree_node(tree_node)
        self.node_for(tree_node).circle.set_color(manim.RED)

    def node_position_animation(self, tree):
        super().node_position_animation(tree)

        animation = []
        def rec_color(tree_node):
            if not tree_node:
                return
            animation.append(self.node_for(tree_node).circle.animate.set_color(manim.RED if tree_node.color_ == Color.RED else manim.DARK_GRAY))
            rec_color(tree_node.children_[Dir.LEFT.value])
            rec_color(tree_node.children_[Dir.RIGHT.value])

        rec_color(tree.root)
        self.flush_animation(animation)


    

class RBTree(BST):

    def new_node(self, value)->RBNode:
        return RBNode(value)

    def remove(self, value)->bool:
        to_delete_node = self.find_node(value, False)

        if not to_delete_node:
            return False

        in_order_successor = to_delete_node.in_order_successor()

        two_children = [None,None]
        if in_order_successor:
            in_order_successor.color_, to_delete_node.color_ = to_delete_node.color_ ,in_order_successor.color_
            two_children = in_order_successor.children_


        super().remove(value)

        if self.root is None:
            return True

        if to_delete_node.color_ == Color.RED:
            return True

        # deleting black, find if we can use sparse red node to complete it
        lowest = to_delete_node

        first_iteration = True
        while lowest != self.root:

            assert lowest.color_ == Color.BLACK

            if first_iteration and two_children[Dir.Right.value]:
                assert two_children[Dir.RIGHT.value].color_ == Color.RED
                two_children[Dir.RIGHT.value].color_ = Color.BLACK
                self.animation_callback.node_position_animation(self)
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
            self.check(self.root, False)
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

        ret = super().insert(value)

        if not ret :
            return ret


        to_fix_node = self.find_node(value, with_animation=False)

        while to_fix_node:
            to_fix_node = self.insert_fix(to_fix_node)
            self.animation_callback.node_position_animation(self)

        self.check(self.root, True)

        return True

    def check(self,root_node, check_color= False):
        super().check(root_node)
        if not root_node:
            return
        
        for dir in Dir:
            child = root_node.children_[dir.value]
            if not child:
                continue

            if root_node != child.parent_:
                pdb.set_trace()
            if check_color:
                assert not (root_node.color_  == Color.RED and child.color_ == Color.RED)



class RbtInsert1(Scene):
    def construct(self):
        callback = RBTreeAnimationCallback(self)
        #callback = AnimationCallback()
        rbt = RBTree(callback)

        rand_data = list(range(20))
        random.shuffle(rand_data)
        rand_data =  [7,2,10,16,15,3,19,14,17,18,11]
        #rand_data = [0,7,3]
        for i in rand_data:
            rbt.insert(i)
        self.wait(1)


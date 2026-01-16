from bst import TreeNode,Dir,BST,BSTAnimationCallback
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


    def insert(self, value)->bool:

        ret = super().insert(value)

        if not ret :
            return ret


        new_node = self.find_node(value, with_animation=False)

        while new_node:
            assert new_node.color_ == Color.RED

            if new_node == self.root:
                self.animation_callback.node_position_animation(self)
                return ret


            parent = new_node.parent_
            assert parent

            if parent.color_ == Color.BLACK:
                return True

            if parent == self.root:
                parent.color_ = Color.BLACK
                self.animation_callback.node_position_animation(self)
                return True
            # double red and have grandparent
            grandparent = parent.parent_
            assert grandparent
            assert grandparent.color_ is Color.BLACK

            parent_dir = Dir(int(parent == grandparent.children_[Dir.RIGHT.value]))
            uncle = grandparent.children_[1 - parent_dir.value]

            grandparent_is_root = grandparent == self.root
            if not uncle:
                #      B
                #     /
                #    R
                #   /
                #  R 
                #   
                #   

                new_sub_root = grandparent.rotate(Dir(1 - parent_dir.value))
                #self.animation_callback.node_position_animation(self)
                # recolor G and P
                grandparent.color_ = Color.RED
                parent.color_ = Color.BLACK

                if grandparent_is_root:
                    self.root = new_sub_root

                self.animation_callback.node_position_animation(self)
                return True

            # has uncle
            if uncle.color_ == Color.BLACK:
                #    G(B)                P(B)
                #   /    \               /   \
                #  P(R)   U(B)   =>    L(R)  G(R)
                #  /  \    /  \               /   \
                #L(R) S(B) .  .. ..         S(B)   U(B)
                new_sub_root = grandparent.rotate(Dir(1 - parent_dir.value))
                grandparent.color_ = Color.RED
                parent.color_ = Color.BLACK

                if grandparent_is_root:
                    self.root = new_sub_root

                self.animation_callback.node_position_animation(self)
                return True
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
            new_node = grandparent
            self.animation_callback.node_position_animation(self)

        assert False

class RbtInsert1(Scene):
    def construct(self):
        callback = RBTreeAnimationCallback(self)
        rbt = RBTree(callback)

        for i in range(10):
            rbt.insert(i)
        self.wait(1)


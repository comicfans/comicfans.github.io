from bst import TreeNode,Dir
from enum import Enum
from typing import Tuple
import manim
from manim import Animation,Scene,AniContext

class Color(Enum):
    BLACK = 0
    RED = 1

class RBNode(TreeNode):
    def set_color(self, color: Color, animation: list[Animation]):
        if self.color_ == color:
            return []

        self.color_ = color
        return self.ani_node().set_color(manim.GRAY if color == Color.BLACK else manim.RED, animation)

class RBT:

    def insert(self, value)->bool:
        animation = []

        new_node = Node(value, None, self, animation)

        self.flush_animation(animation)

        if self.root is None:
            self.root = new_node
            self.node_position_animation(animation)
            return True

        parent,dir,node = self.find_pos(self.root, value)
        if parent.children_[dir.value]:
            # we found duplicated value
            return False

        parent.set_child(dir, new_node, animation)
        self.node_position_animation(animation)

        while new_node:
            assert new_node.color_ == Color.RED

            parent = new_node.parent_
            assert parent

            if parent.color_ == Color.BLACK:
                self.flush_animation(animation)
                return True

            if parent == self.root:
                parent.set_color(Color.BLACK, animation)
                self.flush_animation(animation)
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

                new_sub_root = grandparent.rotate(Dir(1 - parent_dir.value), animation)
                # recolor G and P
                grandparent.set_color(Color.RED,animation)
                parent.set_color(Color.BLACK,animation)

                if grandparent_is_root:
                    self.root = new_sub_root

                self.node_position_animation(animation)
                return True

            # has uncle
            if uncle.color == Color.BLACK:
                #    G(B)                P(B)
                #   /    \               /   \
                #  P(R)   U(B)   =>    L(R)  G(R)
                #  /  \    /  \               /   \
                #L(R) S(B) .  .. ..         S(B)   U(B)
                grandparent.rotate(Dir(1 - parent_dir),animation)
                grandparent.set_color(Color.RED,animation)
                parent.set_color(Color.BLACK,animation)

                if grandparent_is_root:
                    self.root = new_sub_root

                self.flush_animation(animation)
                self.node_position_animation()
                return True
            # uncle is red
            #             G(B)
            #            /   \
            #          P(R)   U(R)
            #          /
            #        L(R)
            #
            #
            grandparent.set_color(Color.RED,animation)
            parent.set_color(Color.BLACK,animation)
            uncle.set_color(Color.BLACK,animation)
            new_node = grandparent

        assert False

class RbtInsert1(Scene):
    def construct(self):
        ani_context = AniContext(self)
        rbt = RBT(ani_context)
        rbt.insert(0)
        #pdb.set_trace()
        rbt.insert(1)
        #pdb.set_trace()
        rbt.insert(2)


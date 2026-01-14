from manim import Circle,Text,VGroup,Line,always_redraw,Animation,Scene,Create,Rectangle
import pdb
from enum import Enum
from typing import Tuple
import numpy as np
import manim

CIRCLE_RADIUS = 0.35

class Dir (Enum):
    LEFT=0
    RIGHT=1

class Node:
    def __init__(self, value, parent, tree, animation:list[Animation]):
        self.value = value
        self.parent_ = parent 
        self.children_ = [None, None]
        self.parent_dir_ = [None, None]
        self.tree_ = tree

        animation.append(Create(self.tree_.ani_context.new_node(self).group_node))



    def ani_node(self):
        context = self.tree_.ani_context
        return context.node_for(self.value)


    def set_child(self, dir: Dir, node):
        self.children_[dir.value] = node
        node.parent_ = self

    def swap(self, other):
        if self == other:
            return
        self.children,other.children = other.children,self.children 
        self.parent_dir,other.parent_dir = other.parent_dir,self.parent_dir
        self.redirect_children_parent()
        other.redirect_children_parent()
        
    def redirect_children_parent(self):
        for dir in Dir:
            if self.children_[dir.value]:
                self.children_[dir.value].parent_dir[0] = self

    def rotate(self, dir: Dir):

        to_move_up = self.children_[1 - dir.value]
        assert to_move_up
        #
        #       SELF
        #       /  \
        #    LEFT  RIGHT
        #
        #    right rotation
        #

        parent = self.parent_
        self_dir = Dir(int(self == parent.children_[Dir.RIGHT.value])) if parent else None
        move_nephew = to_move_up.children_[dir.value]

        self.parent_ = to_move_up
        to_move_up.children_[dir.value] = self
        to_move_up.parent_ = parent

        self.children_[1-dir.value] = move_nephew

        if parent:
            parent.children_[self_dir.value] = to_move_up

        return to_move_up



class AniContext:
    def __init__(self,scene):
        self.scene = scene
        self.node_map = {}

    def node_for(self, value):
        return self.node_map[str(value)]

    def new_node(self,tree_node):
        assert str(tree_node.value) not in self.node_map
        ani_node = AniNode(self, tree_node)
        self.node_map[str(tree_node.value)] = ani_node
        return ani_node


    def delete_node(self, value):
        pass




class AniNode:

    def draw_line(self,dir:Dir)->Line:

        #if self.tree_node.value == 1 and dir == Dir.LEFT and self.tree_node.children_[dir.value]:
        #    pdb.set_trace()

        if not self.tree_node.children_[dir.value]:
            return Line(self.group_node.get_bottom(),self.group_node.get_bottom())

        target_ani = self.ani_context.node_for(self.tree_node.children_[dir.value].value)

        return Line(self.group_node.get_bottom(),
                    target_ani.group_node.get_top())



    def __init__(self, ani_context, tree_node):
        self.ani_context = ani_context
        self.tree_node = tree_node
        self.circle = Circle(radius=CIRCLE_RADIUS, stroke_color = manim.RED)
        self.text = Text(str(tree_node.value), font_size = 24, color = manim.RED)
        self.text.move_to(self.circle)
        self.group_node = VGroup(self.circle, self.text)
        self.group_node.move_to(manim.UP * 2)
        self.children_edges = []
        for value in Dir:
            self.children_edges.append(always_redraw(
                                       lambda value=value: self.draw_line(value)))
            self.ani_context.scene.add(self.children_edges[-1])
        

    def set_color(self, manim_color, animation : list[Animation]):
        for obj in [self.circle,self.text]:
            animation.append(obj.animate.set_color(manim_color))



    def move_to(self, pos, animation: list[Animation]):
        animation.append(self.group_node.animate.move_to(pos))



class BST:

    def __init__(self, ani_context: AniContext):
        self.root = None
        self.ani_context = ani_context
        width,height = BST.rect_width_height(0)
        self.rect = Rectangle(width = width, height = height).move_to(BST.rect_pos(height))
        ani_context.scene.add(self.rect)


    def find_pos(self, value, show_animation)-> Tuple[Node, dir, Node]:
        animation = []
        parent = None
        next_try = self.root
        child_dir = None

        while next_try:
            next_try
            if value == next_try.value:
                animation.append(self.ani_context.node_for(value).group_node.animate.move_to(self.ani_context.node_for(next_try.value).group_node.get_top()))
                return (parent, child_dir, next_try)
            parent = next_try
            child_dir = Dir.LEFT if value < parent.value else Dir.RIGHT
            target_node = self.ani_context.node_for(next_try.value).group_node
            animation.append(self.ani_context.node_for(value).group_node.animate.move_to(target_node.get_left() - np.array([CIRCLE_RADIUS,0,0]) if child_dir is Dir.LEFT else target_node.get_right() + np.array([CIRCLE_RADIUS,0,0])))
            next_try = parent.children_[child_dir.value]
            if show_animation:
                self.flush_animation(animation)

        if show_animation:
            self.flush_animation(animation)
        return (parent, child_dir, next_try)


    @staticmethod
    def depth(node: Node)->int:
        if not node:
            return 0
        
        return 1+max(BST.depth(node.children_[Dir.LEFT.value]),
                     BST.depth(node.children_[Dir.RIGHT.value]))

    def assign_position(self, root, offset, total_depth, current_depth, dir:Dir| None, animation):
        if not root:
            return None

        horizontal_base = offset + (0 if not dir else pow(2, total_depth - 1 - current_depth) * (-1 if dir == Dir.LEFT else 1))

        pos = current_depth * manim.DOWN + horizontal_base * manim.RIGHT
        animation.append(self.ani_context.node_for(root.value).group_node.animate.move_to(pos))

        self.assign_position(root.children_[Dir.LEFT.value],
                                        horizontal_base, total_depth, current_depth +1, Dir.LEFT, animation)

        self.assign_position(root.children_[Dir.RIGHT.value],
                                        horizontal_base, total_depth, current_depth +1, Dir.RIGHT,animation)
        
    @staticmethod
    def rect_width_height(self_depth):
        return (pow(2,max(0,self_depth-1)) * manim.RIGHT[0], max(self_depth,1)* manim.UP[1])

    @staticmethod
    def rect_pos(height):
        return np.array([0,-height/2,0])

    def node_position_animation(self, animation):
        self_depth = BST.depth(self.root)
        # root sit at 0,0
        self.assign_position(self.root, 0, self_depth, 0, None, animation)


        width,height = BST.rect_width_height(self_depth)

        animation.append(self.rect.animate.move_to(BST.rect_pos(height)))
        animation.append(self.rect.animate.set_height(height))
        animation.append(self.rect.animate.set_width(width))


        self.flush_animation(animation)

    def flush_animation(self, animation:list[Animation], run_time = 0.5, wait_after_run = 0.1):
        if not len(animation):
            return
        self.ani_context.scene.play(*animation, run_time = run_time)
        self.ani_context.scene.wait(wait_after_run)
        animation.clear()

    def new_node(self, value, animation):
        return Node(value, None, self,animation)

    def rotate(self, value_or_node, dir:Dir):
        node = value_or_node
        if not isinstance(value_or_node, Node):
            node = self.find_pos(value_or_node,False)[2]

        node_is_root = (node == self.root)
            
        new_root = node.rotate(dir)

        if node_is_root:
            self.root = new_root

        self.node_position_animation([])

    def insert(self, value)->bool:
        animation = []
        new_node = self.new_node(value, animation)
        self.flush_animation(animation)

        if self.root is None:
            self.root = new_node
            self.node_position_animation(animation)
            return True

        parent,dir,node = self.find_pos(value, True)
        if parent.children_[dir.value]:
            # we found duplicated value
            return False

        parent.set_child(dir, new_node)
        self.node_position_animation(animation)
        return True

class BSTInsert(Scene):
    def construct(self):
        ani_context = AniContext(self)
        bst = BST(ani_context)
        bst.insert(0)
        bst.insert(1)
        bst.insert(2)
        bst.rotate(1, Dir.LEFT)
        self.wait(1)



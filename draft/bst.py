from manim import Circle,Text,VGroup,Line,always_redraw,Animation,Scene,Create,Rectangle,FadeOut
from manim.typing import Point3D
from copy import deepcopy
from dataclasses import dataclass
import random
import pdb
from enum import Enum
from typing import Tuple, Any
import numpy as np
import manim

CIRCLE_RADIUS = 0.35
NODE_INIT_POS = manim.UP * 2
ANIMATION_RUNTIME = 0.5

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
        return context.node_for(self)


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

    def node_for(self, node: Any):
        return self.node_map[node]

    def new_node(self,tree_node):
        assert tree_node not in self.node_map

        ani_node = AniNode(self, tree_node)
        self.node_map[tree_node] = ani_node

        return ani_node


    def delete_node(self, tree_node,animation :list[Animation]):
        animation.append(tree_node.group_node.animate.move_to(NODE_INIT_POS))
        #animation.append(tree_node.group_node.animate.set_optical(0))




class AniNode:



    def update_line(self, line, dt, dir):

        target_node = self.tree_node.children_[dir.value]
        if not target_node:
            target_pos = self.group_node.get_bottom()
        else:
            target_ani = self.ani_context.node_for(target_node)
            target_pos = target_ani.group_node.get_top()

        current_end = self.group_node.get_bottom()
        new_end = current_end + (target_pos - current_end) * min(dt *2 ,1)

        line.put_start_and_end_on(self.group_node.get_bottom(), new_end)

    def __init__(self, ani_context, tree_node):
        self.ani_context = ani_context
        self.tree_node = tree_node
        self.circle = Circle(radius=CIRCLE_RADIUS, 
                             stroke_color = manim.WHITE
                             )
        self.text = Text(str(tree_node.value), font_size = 24
                         #, color = manim.RED
                         )
        self.text.move_to(self.circle)
        self.children_edges = []
        for dir in Dir:
            line = Line(self.circle.get_bottom(),self.circle.get_bottom())
            self.children_edges.append(line)
            #line.add_updater(lambda line,dt,dir=dir: self.update_line(line,dt,dir))
            self.ani_context.scene.add(self.children_edges[-1])
        
        self.group_node = VGroup(self.circle, self.text, *self.children_edges)
        self.group_node.move_to(NODE_INIT_POS)

    def set_color(self, manim_color, animation : list[Animation]):
        for obj in [self.circle,self.text]:
            animation.append(obj.animate.set_color(manim_color))



    def move_to(self, pos, animation: list[Animation]):
        animation.append(self.group_node.animate.move_to(pos))


class PositionNode:

    def __init__(self):

        self.merged_range: list[PositionNode]=[] # every tuple is [left, right)
        # left and right sub-tree
        self.children:list[Any] = [None, None]

        self.tree_node: Node = None # corresponding tree node

    def total_range(self)->Tuple[float,float]:
        left = float('inf')
        right = float('-inf')
        for r in self.merged_range:
            left = min(left, r[0])
            right = max(right, r[1])
        return left, right

    def apply_offset(self, offset:float):
        self.merged_range = [(left + offset, right + offset) for (left, right) in self.merged_range]
        for dir in Dir:
            child = self.children[dir.value]
            if child:
                child.apply_offset(offset)

    @staticmethod
    def merge_left_right(left, right, tree_node: Node):

        ret = PositionNode()
        ret.tree_node = tree_node

        assert tree_node
        if not left and not right:
            ret.merged_range = [(0,1)]
            return ret

        if not left or not right:
            offset = 0.5 if right else -0.5
            child = right if right else left
            child.apply_offset(offset)
            ret.children[(Dir.RIGHT if right else Dir.LEFT).value] = child
            ret.merged_range = deepcopy(child.merged_range)
            ret.merged_range.append((0,1))
            return ret

        # first find minimal right offset to avoid overlapping

        min_offset = float('-inf')

        left_len = len(left.merged_range)
        right_len = len(right.merged_range)
        for i in range(min(left_len, right_len)):
            left_right = left.merged_range[-1-i][1]
            right_left = right.merged_range[-1-i][0]
            this_offset = left_right - right_left
            min_offset = max(min_offset, this_offset)

        # then we know left and right+min_offset will not overlap
        # new root sit at middle of left+right
        left.apply_offset(-min_offset/2)
        right.apply_offset(min_offset/2)
        ret.children[Dir.LEFT.value] = left
        ret.children[Dir.RIGHT.value] = right

        longer,shorter = (left,right) if left_len > right_len else (right,left)

        diff_len = len(longer.merged_range) - len(shorter.merged_range)
        for i in range(max(left_len,right_len) - min(left_len,right_len)):
            # copy longer merged range
            ret.merged_range.append(longer.merged_range[i])

        for i in range(len(shorter.merged_range)):
            longer_pos = diff_len + i
            ret.merged_range.append((min(shorter.merged_range[i][0], longer.merged_range[longer_pos][0]),
                                     max(shorter.merged_range[i][1], longer.merged_range[longer_pos][1])))
        ret.merged_range.append((0,1))
        return ret


def fill_width(root) -> PositionNode:
    if not root:
        return None

    left_pos= fill_width(root.children_[Dir.LEFT.value])
    right_pos= fill_width(root.children_[Dir.RIGHT.value])

    merged = PositionNode.merge_left_right(left_pos, right_pos, root)
    return merged

class BST:

    def __init__(self, ani_context: AniContext):
        self.root = None
        self.ani_context = ani_context
        self.rect = Rectangle(width = 5, height = 1)
        ani_context.scene.add(self.rect)


    def find_pos(self, value_or_node, show_animation)-> Tuple[Node, dir, Node]:
        animation = []
        parent = None
        next_try = self.root
        child_dir = None

        value = value_or_node.value if isinstance(value_or_node, Node) else value_or_node

        while next_try:
            next_try
            if value == next_try.value:
                if show_animation:
                    #when show animation, this must be node
                    animation.append(self.ani_context.node_for(next_try).text.animate.set_color(manim.RED))
                    animation.append(self.ani_context.node_for(value_or_node).group_node.animate.move_to(self.ani_context.node_for(next_try).circle.get_top()))
                    self.flush_animation(animation)
                    animation.append(self.ani_context.node_for(next_try).text.animate.set_color(manim.WHITE))
                    self.flush_animation(animation)

                return (parent, child_dir, next_try)
            parent = next_try
            child_dir = Dir.LEFT if value < parent.value else Dir.RIGHT
            target_node = self.ani_context.node_for(next_try).circle
            next_try = parent.children_[child_dir.value]
            if show_animation:
                animation.append(self.ani_context.node_for(value_or_node).group_node.animate.move_to(target_node.get_left() - np.array([CIRCLE_RADIUS,0,0]) if child_dir is Dir.LEFT else target_node.get_right() + np.array([CIRCLE_RADIUS,0,0])))
                animation.append(self.ani_context.node_for(parent).text.animate.set_color(manim.RED))
                self.flush_animation(animation)
                animation.append(self.ani_context.node_for(parent).text.animate.set_color(manim.WHITE))

        if show_animation:
            self.flush_animation(animation)
        return (parent, child_dir, next_try)


    @staticmethod
    def depth(node: Node)->int:
        if not node:
            return 0
        
        return 1+max(BST.depth(node.children_[Dir.LEFT.value]),
                     BST.depth(node.children_[Dir.RIGHT.value]))

    def assign_position(self, position_node:PositionNode, animation:list[Animation],current_depth = 0):
        if not position_node:
            return


        children_pos = [None,None]

        for dir in Dir:
            children_pos[dir.value] = self.assign_position(position_node.children[dir.value],animation,
                                                           current_depth +1)
        
        pos = current_depth * manim.DOWN + position_node.merged_range[-1][0] * manim.RIGHT
        ani_node = self.ani_context.node_for(position_node.tree_node)
        animation.append(ani_node.circle.animate.move_to(pos))
        animation.append(ani_node.text.animate.move_to(pos))
        half = np.array([0, -CIRCLE_RADIUS,0])
        for dir in Dir:
            target_pos = pos + half
            if position_node.children[dir.value]:
                target_pos = children_pos[dir.value] - half

            assert target_pos is not None

            from_pos = pos + half
            if np.all(from_pos == target_pos):
                # manim error
                target_pos = target_pos +manim.UP * 0.01

            animation.append(ani_node.children_edges[dir.value].animate.put_start_and_end_on(pos + half,
                                                                                             target_pos + manim.UP * 0.01))

        return pos


    @staticmethod
    def rect_pos(height):
        return np.array([0,-height/2,0])



    def node_position_animation(self, animation):

        position_node = fill_width(self.root)

        self_depth = BST.depth(self.root)
        new_range = position_node.total_range()

        animation = []
        self.assign_position(position_node,animation)


        screen_height = max(self_depth,1) * manim.UP[1]
        screen_left = (new_range[0]-0.5) * manim.RIGHT[0]
        screen_right = (new_range[1]-0.5) * manim.RIGHT[0]

        new_center_y = -screen_height / 2 + CIRCLE_RADIUS*1.5
        new_center_x = (screen_left + screen_right) / 2

        #animation.append(self.rect.animate.stretch_to_fit_width(screen_right - screen_left).stretch_to_fit_height(screen_height).move_to(np.array([0,new_center_x,0])))
        animation.append(self.rect.animate.stretch_to_fit_width(screen_right - screen_left).stretch_to_fit_height(screen_height).move_to(np.array([new_center_x,new_center_y,0])))

        self.flush_animation(animation)

    def flush_animation(self, animation:list[Animation], run_time = ANIMATION_RUNTIME, wait_after_run = 0.1):
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
            node = self.find_pos(value_or_node, False)[2]

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

        parent,dir,node = self.find_pos(new_node, True)

        if node and node.value == value:
            # we found duplicated value
            self.ani_context.delete_node(new_node.ani_node(),animation)
            self.flush_animation(animation)
            self.ani_context.scene.play(FadeOut(new_node.ani_node().group_node),run_time = ANIMATION_RUNTIME)
            return False

        parent.set_child(dir, new_node)
        self.node_position_animation(animation)
        return True

class BSTInsert(Scene):
    def construct(self):
        ani_context = AniContext(self)
        bst = BST(ani_context)
        #bst.insert(0)
        #bst.insert(-5)
        #bst.insert(5)
        #bst.insert(-3)
        #bst.insert(3)
        ##bst.rotate(1, Dir.LEFT)
        #self.wait(1)
        #return
        insert_value = [0, -5, 5, -7, -3, 3, 7]

        #pdb.set_trace()
        for i in insert_value:
            bst.insert(i)

        bst.rotate(0,Dir.LEFT)
        self.wait(1)


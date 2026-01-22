from manim import Circle,Text,VGroup,Line,always_redraw,Animation,Scene,Create,Rectangle,FadeOut
import random
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

class TreeNode:
    def __init__(self, value):
        self.value = value
        self.parent_ = None
        self.children_ = [None, None]
        self.parent_dir_ = [None, None]

    def __repr__(self):
        return f"{self.value}, parent:{self.parent_.value if self.parent_ else 'none'}  children: [{self.children_[0].value if self.children_[0] else 'none' }, {self.children_[1].value if self.children_[1] else 'none'}]"

    def disconnect(self):

        assert self.children_[Dir.LEFT.value] is None or self.children_[Dir.RIGHT.value] is None

        if self.parent_:
            self_side = Dir(int(self == self.parent_.children_[Dir.RIGHT.value]))
            self.parent_.set_child(self_side, self.children_[Dir.LEFT.value] or self.children_[Dir.RIGHT.value])
        else:
            for dir in Dir:
                if self.children_[dir.value]:
                    self.children_[dir.value].parent_ = None

        for dir in Dir:
            self.children_[dir.value] = None

        self.parent_ = None

    def set_child(self, dir: Dir, node):
        self.children_[dir.value] = node
        if node:
            node.parent_ = self

    def swap(self, to_swap):

        assert to_swap
        assert self != to_swap

        self.children_,to_swap.children_ = to_swap.children_,self.children_
        self.parent_,to_swap.parent_ = to_swap.parent_,self.parent_

        to_check = [self, to_swap]
        for idx, test in enumerate(to_check):
            another = to_check[1-idx]
            if test.parent_ == test:
                test.parent_ = another
            elif test.parent_:
                old_side = Dir(int(another== test.parent_.children_[Dir.RIGHT.value]))
                test.parent_.children_[old_side.value] = test

            for dir in Dir:
                if test.children_[dir.value] == test:
                    test.children_[dir.value] = another


        self.redirect_children_parent()
        to_swap.redirect_children_parent()
        # two node might point to each other, then there'll be self-loop in parent/children
        # now break them
        
    def in_order_successor(self):
        ret = self.children_[Dir.RIGHT.value]
        while ret and ret.children_[Dir.LEFT.value]:
            ret = ret.children_[Dir.LEFT.value]

        return ret



        
    def redirect_children_parent(self):
        for dir in Dir:
            if self.children_[dir.value]:
                self.children_[dir.value].parent_ = self

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

        to_move_up.set_child(dir, self)

        self.set_child(Dir(1-dir.value), move_nephew)
        
        if parent:
            parent.set_child(self_dir, to_move_up)
        else:
            to_move_up.parent_ = None

        return to_move_up






class AniNode:

    def __init__(self, scene, value, radius = CIRCLE_RADIUS):
        self.scene = scene
        self.circle = Circle(radius=radius, 
                             stroke_color = manim.WHITE
                             )
        self.text = Text(str(value), font_size = 24
                         #, color = manim.RED
                         )
        self.text.move_to(self.circle)
        self.parent_edge = Line(self.circle.get_top(),self.circle.get_top())
        self.scene.add(self.parent_edge)
        
        self.group_node = VGroup(self.circle, self.text, *self.parent_edge)
        self.group_node.move_to(NODE_INIT_POS)

    def set_color(self, manim_color, animation : list[Animation]):
        for obj in [self.circle,self.text]:
            animation.append(obj.animate.set_color(manim_color))



    def move_to(self, pos, animation: list[Animation]):
        animation.append(self.group_node.animate.move_to(pos))


class LayoutPositionNode:

    def __init__(self):

        self.merged_range: list[LayoutPositionNode]=[] # every tuple is [left, right)
        # left and right sub-tree
        self.children:list[Any] = [None, None]

        self.tree_node: TreeNode = None # corresponding tree node

    @staticmethod
    def total_range(node)->Tuple[float,float]:

        if not node:
            return [0,1]


        left = float('inf')
        right = float('-inf')
        for r in node.merged_range:
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
    def merge_left_right(left, right, tree_node: TreeNode):

        ret = LayoutPositionNode()
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

    @staticmethod
    def fill_width(root:TreeNode) -> Any:
        if not root:
            return None
    
        left_pos= LayoutPositionNode.fill_width(root.children_[Dir.LEFT.value])
        right_pos= LayoutPositionNode.fill_width(root.children_[Dir.RIGHT.value])
    
        merged = LayoutPositionNode.merge_left_right(left_pos, right_pos, root)
        return merged

class AnimationCallback:
    def delete_node(self,tree_node):
        pass

    def init_callback(self, tree):
        pass

    def on_new_tree_node(self, tree_node):
        pass

    def on_search_begin(self, value):
        pass

    def on_search_progress(self, value, parent, current):
        pass

    def on_search_end(self, value, duplicated_found):
        pass


    def node_position_animation(self, tree):
        pass

class BSTAnimationCallback(AnimationCallback):


    def node_for(self, tree_node: Any):
        return self.node_map[tree_node]




    def delete_node(self, tree_node):
        animation = []
        del_ani = self.node_for(tree_node)
        animation.append(del_ani.group_node.animate.move_to(NODE_INIT_POS))
        # also animation edge disappear
        animation.append(del_ani.parent_edge.animate.put_start_and_end_on(NODE_INIT_POS, NODE_INIT_POS))
        self.flush_animation(animation)
        animation.append(FadeOut(del_ani.group_node))
        self.flush_animation(animation)
        #animation.append(tree_node.group_node.animate.set_optical(0))


    def __init__(self, scene: Scene):
        self.scene = scene
        self.node_map = {}
        self.enabled = True

    def init_callback(self, tree):
        self.rect = Rectangle(width = 1, height = 1)
        self.scene.add(self.rect)

    def flush_animation(self, animation:list[Animation], run_time = ANIMATION_RUNTIME, wait_after_run = 0.1):

        if not len(animation):
            return

        if not self.enabled:
            animation.clear()
            return

        self.scene.play(*animation, run_time = run_time)
        self.wait(wait_after_run)
        animation.clear()

    def wait(self, wait_after_run = 0.1):
        self.scene.wait(wait_after_run)


    def on_new_tree_node(self, tree_node):

        assert tree_node not in self.node_map
        self.node_map[tree_node] = AniNode(self.scene, tree_node.value)
        animation = [Create(self.node_for(tree_node).group_node)]
        self.flush_animation(animation)

    def on_search_begin(self, value):
        self.search_animation = []
        self.search_ani_node = AniNode(self.scene, value, CIRCLE_RADIUS * 0.75)

    def on_search_progress(self, value, parent, current):

        assert current

        compare_ani_node = self.node_for(current)

        if value == current.value:
            #when show animation, this must be node
            self.search_animation.append(compare_ani_node.text.animate.set_color(manim.RED))
            self.search_animation.append(self.search_ani_node.group_node.animate.move_to(compare_ani_node.circle.get_top()))
            self.flush_animation(self.search_animation)
            return


        self.search_animation.append(compare_ani_node.text.animate.set_color(manim.RED))
        target_node = compare_ani_node.circle

        offset = CIRCLE_RADIUS * 0.5
        target_pos = target_node.get_left() - np.array([offset,0,0]) if value < current.value else target_node.get_right() + np.array([offset,0,0])
        target_pos = target_pos - np.array([0,offset,0])

        self.search_animation.append(self.search_ani_node.group_node.animate.move_to(target_pos))
        self.flush_animation(self.search_animation)
        self.search_animation.append(compare_ani_node.text.animate.set_color(manim.WHITE))

    def on_search_end(self, value, duplicated_found):
        # we found duplicated value
        self.search_animation.append(FadeOut(self.search_ani_node.group_node))
        self.flush_animation(self.search_animation)
        del self.search_animation
        del self.search_ani_node

    def on_delete_node(self, tree_node):
        to_delete_ani = self.node_for(tree_node)
        animation = [FadeOut(to_delete_ani.group_node)]
        self.flush_animation(animation)

    def assign_position(self, parent_pos ,position_node:LayoutPositionNode, animation:list[Animation],current_depth = 0):
        if not position_node:
            return


        children_pos = [None,None]
        pos = current_depth * manim.DOWN + position_node.merged_range[-1][0] * manim.RIGHT

        for dir in Dir:
            children_pos[dir.value] = self.assign_position(pos, position_node.children[dir.value],animation,
                                                           current_depth +1)
        
        ani_node = self.node_for(position_node.tree_node)
        animation.append(ani_node.circle.animate.move_to(pos))
        animation.append(ani_node.text.animate.move_to(pos))
        half = np.array([0, -CIRCLE_RADIUS,0])

        target_pos = pos - half
        if parent_pos is not None:
            target_pos = parent_pos + half

        assert target_pos is not None

        from_pos = pos + half
        if np.all(from_pos == target_pos):
            # manim error
            target_pos = target_pos +manim.UP * 0.01

        animation.append(ani_node.parent_edge.animate.put_start_and_end_on(pos - half,
                                                                           target_pos + manim.UP * 0.01))

        return pos


    def node_position_animation(self, tree):
        position_node = LayoutPositionNode.fill_width(tree.root)

        self_depth = BST.depth(tree.root)
        new_range = LayoutPositionNode.total_range(position_node)

        animation = []
        self.assign_position(None,position_node,animation)


        screen_height = max(self_depth,1) * manim.UP[1]
        screen_left = (new_range[0]-0.5) * manim.RIGHT[0]
        screen_right = (new_range[1]-0.5) * manim.RIGHT[0]

        new_center_y = -screen_height / 2 + CIRCLE_RADIUS*1.5
        new_center_x = (screen_left + screen_right) / 2

        #animation.append(self.rect.animate.stretch_to_fit_width(screen_right - screen_left).stretch_to_fit_height(screen_height).move_to(np.array([0,new_center_x,0])))
        animation.append(self.rect.animate.stretch_to_fit_width(screen_right - screen_left).stretch_to_fit_height(screen_height).move_to(np.array([new_center_x,new_center_y,0])))

        self.flush_animation(animation)

class DummyAnimationCallback(AnimationCallback):
    pass

class BST:

    def __init__(self, animation_callback: AnimationCallback):
        self.root = None
        self.animation_callback = animation_callback
        self.animation_callback.init_callback(self)

    def find_node(self, value, with_animation)->TreeNode:
        if with_animation:
            return self.find_pos(value)[2]


        temp = self.animation_callback
        self.animation_callback = DummyAnimationCallback()
        ret = self.find_pos(value)[2]
        self.animation_callback = temp
        return ret

    def find_pos(self, value)-> Tuple[TreeNode, dir, TreeNode]:
        parent = None
        next_try = self.root
        child_dir = None

        self.animation_callback.on_search_begin(value)

        while next_try:
            self.animation_callback.on_search_progress(value, parent, next_try)
            if value == next_try.value:
                self.animation_callback.on_search_end(value, True)
                return (parent, child_dir, next_try)
            parent = next_try
            child_dir = Dir.LEFT if value < parent.value else Dir.RIGHT
            next_try = parent.children_[child_dir.value]


        self.animation_callback.on_search_end(value, False)
        return (parent, child_dir, next_try)




    def new_node(self, value):
        return TreeNode(value)


    def rotate(self, node, dir:Dir)->TreeNode:

        node_is_root = (node == self.root)
        new_root = node.rotate(dir)

        if node_is_root:
            self.root = new_root

        self.check()
        self.animation_callback.node_position_animation(self)
        return new_root


    def remove(self, value, fill_before_remove = {})->bool:

        to_delete_node = self.find_node(value, True)

        if not to_delete_node:
            return False

        changing_root = to_delete_node == self.root
        in_order_successor = to_delete_node.in_order_successor()

        self_dir = None if not to_delete_node.parent_ else Dir.LEFT if to_delete_node== to_delete_node.parent_.children_[Dir.LEFT.value] else Dir.RIGHT

        def fill_info(to_delete_node):
            fill_before_remove['parent'] = None if to_delete_node.parent_ is None else to_delete_node.parent_
            fill_before_remove['right_child'] = to_delete_node.children_[Dir.RIGHT.value]
            fill_before_remove['self_dir'] = None if to_delete_node.parent_ is None else Dir.LEFT if to_delete_node== to_delete_node.parent_.children_[Dir.LEFT.value] else Dir.RIGHT

        fill_info(to_delete_node)

        if in_order_successor :
            to_delete_node.swap(in_order_successor)
            if changing_root:
                self.root = in_order_successor


            self.animation_callback.node_position_animation(self)
            self.animation_callback.wait(0.2)

            fill_info(to_delete_node)

            to_delete_node.disconnect()
            self.animation_callback.delete_node(to_delete_node)

            self.animation_callback.node_position_animation(self)
            self.check()
            return True

        # no in-order successor, root is left child
        if changing_root:
            self.root = to_delete_node.children_[Dir.LEFT.value]
        to_delete_node.disconnect()
        self.animation_callback.delete_node(to_delete_node)
        self.animation_callback.node_position_animation(self)
        self.check()
        

    def insert(self, value)->bool:
        new_node = self.new_node(value)
        self.animation_callback.on_new_tree_node(new_node)

        if self.root is None:
            self.root = new_node
            self.animation_callback.node_position_animation(self)
            return True

        parent,dir,node = self.find_pos(value)

        if node and node.value == value:
            self.animation_callback.on_delete_node(new_node)
            return False

        parent.set_child(dir, new_node)
        self.animation_callback.node_position_animation(self)
        return True

    @staticmethod
    def depth(node: TreeNode)->int:
        if not node:
            return 0
        
        return 1+max(BST.depth(node.children_[Dir.LEFT.value]),
                     BST.depth(node.children_[Dir.RIGHT.value]))

    def check(self):

        if self.root:
            assert self.root.parent_ is None

        walked = set()
        def do_check(root_node):
            if not root_node:
                return

            assert root_node not in walked
            walked.add(root_node)
            
            for dir in Dir:
                child = root_node.children_[dir.value]
                if not child:
                    continue

                assert root_node == child.parent_
                do_check(child)
        do_check(self.root)

    



class BstInsert(Scene):
    def construct(self):
        animation_callback = BSTAnimationCallback(self)
        bst = BST(animation_callback)

        for i in [3,1,0,2,5,4,6]:
            bst.insert(i)

        self.wait(1)

class BstRemove(Scene):
    def construct(self):
        animation_callback = BSTAnimationCallback(self)

        animation_callback.enabled = False
        bst = BST(animation_callback)

        data = [3,1,0,2,5,4,6]
        for i in data:
            bst.insert(i)



        animation_callback.enabled = True
        animation_callback.node_position_animation(bst)

        for i in [3,4,5,6,1,2,0]:
            bst.remove(i)

        self.wait(1)


class BstBad(Scene):
    def construct(self):
        animation_callback = BSTAnimationCallback(self)
        bst = BST(animation_callback)

        for i in range(4):
            bst.insert(i)

        self.wait(1)


class BstRotate(Scene):
    def construct(self):
        animation_callback = BSTAnimationCallback(self)
        animation_callback.enabled = False
        bst = BST(animation_callback)

        for i in [1,0,2]:
            bst.insert(i)

        animation_callback.enabled = True
        animation_callback.node_position_animation(bst)

        bst.rotate(bst.root, Dir.LEFT)
        self.wait(1)
        bst.rotate(bst.root, Dir.RIGHT)
        self.wait(1)
        bst.rotate(bst.root, Dir.RIGHT)
        self.wait(1)
        bst.rotate(bst.root, Dir.LEFT)
        self.wait(1)


class BstRotateTree(Scene):
    def construct(self):
        animation_callback = BSTAnimationCallback(self)
        animation_callback.enabled = False
        bst = BST(animation_callback)

        for i in [3,5,4,6,1,2,0]:
            bst.insert(i)

        animation_callback.enabled = True
        animation_callback.node_position_animation(bst)


        bst.rotate(bst.root, Dir.LEFT)
        self.wait(1)

        bst.rotate(bst.root, Dir.RIGHT)
        self.wait(1)


        bst.rotate(bst.root, Dir.RIGHT)
        self.wait(1)

        bst.rotate(bst.root, Dir.LEFT)
        self.wait(1)

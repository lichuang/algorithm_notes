# -*- coding: UTF-8 -*-
import random
import unittest

INVALID_KEY = -1

class BPlusTreeBaseNode(object):
  def __init__(self,tree,parent):
    self.num = 0
    self.tree = tree
    self.t = tree.t
    self.keys = []
    self.parent = parent
    self.next = None
    self.prev = None

  def isFull(self):
    return self.num == (self.t * 2 - 1)

  def isEnough(self):
    return self.num >= (self.t - 1)

  def setNext(self, next):
    self.next = next
  
  def getNext(self):
    return self.next

  def setPrev(self, prev):
    self.prev = prev
  
  def getPrev(self):
    return self.prev

  def setNum(self, num):
    self.num = num
  
  def getNum(self):
    return self.num

  def setParent(self, parent):
    self.parent = parent

  def getParent(self):
    return self.parent

  def getKey(self, index):
    return self.keys[index]

  def setKey(self, index, key):
    self.keys[index] = key

class BPlusTreeNode(BPlusTreeBaseNode):
  def __init__(self,tree,parent):
    BPlusTreeBaseNode.__init__(self,tree,parent) 
    t = tree.t
    for i in range(2 * t - 1):
      self.keys.append(INVALID_KEY)

    self.children = []
    for i in range(2 * t):
      self.children.append(None)

  def isLeaf(self):
    return False

  def getChild(self, index):
    return self.children[index]

  def setChild(self, index, child):
    self.children[index] = child

  def getKeyAndChild(self, index):
    return self.keys[index],self.children[index]

  def setKeyAndChild(self, index, packed):
    key, child = packed
    self.keys[index] = key
    self.children[index] = child

  def _findPosition(self, key):
    i = 0
    while (i < self.getNum() and (self.getKey(i) <= key)):
      i += 1
    return i

  # insert (key,,value) into nonfull node
  def _insertNonFull(self, node, key, value):
    pos = node._findPosition(key)

    split,key,left,right = node.getChild(pos).insert(key,value)
    if not split:
      return
    if pos == node.getNum():
      # insert at the rightmost key
      node.setKey(pos,key)
      node.setChild(pos, left)
      node.setChild(pos + 1, right)
      node.setNum(node.getNum() + 1)
    else:
      # insert not at the rightmost key
      node.setChild(node.getNum() + 1,node.getChild(node.getNum()))
      for i in range(node.getNum(),pos, -1):
        node.setKeyAndChild(i, node.getKeyAndChild(i-1))
      node.setKey(pos,key)
      node.setChild(pos, left)
      node.setChild(pos + 1, right)
      node.setNum(node.getNum() + 1)    

  # return split,key,left,right
  def insert(self, key, value):
    if self.isFull(): # node is full,split it
      threshold = self.t
      right = BPlusTreeNode(self.tree, self.parent)

      self.setNext(right)
      right.setPrev(self)
      
      right.setNum(self.getNum() - threshold)
      # copy [t:2t-1] to sibling
      for i in range(0, right.getNum()):
        right.setKeyAndChild(i, self.getKeyAndChild(threshold+i))
      
      right.setChild(right.getNum(), self.getChild(self.getNum()))
      self.setNum(threshold - 1)

      return_key = self.getKey(threshold - 1)
      left = self

      # insert in the appropriate node
      if key < return_key:
        self._insertNonFull(self,key,value)
      else:
        self._insertNonFull(right,key,value)

      return True,return_key,left,right
    else:
      self._insertNonFull(self,key,value)
      return False,INVALID_KEY,None,None
      
  def search(self, key):
    pos = self._findPosition(key)
    if pos == len(self.children):
      return None
    child = self.getChild(pos)
    if child == None:
      return None
    return child.search(key)

  def traverse(self, result):
    for i in range(0, self.getNum() + 1):
      child = self.getChild(i)
      result = child.traverse(result)
    return result

class BPlusTreeLeaf(BPlusTreeBaseNode):
  def __init__(self,tree,parent):
    BPlusTreeBaseNode.__init__(self,tree,parent) 
    t = tree.t
    self.datas = []
    for i in range(2 * t - 1):
      self.keys.append(INVALID_KEY)
      self.datas.append(INVALID_KEY)

  def isLeaf(self):
    return True
  
  def getKeyAndData(self, index):
    return self.keys[index],self.datas[index]

  def setKeyAndData(self, index, packed):
    key, data = packed
    self.keys[index] = key
    self.datas[index] = data
  
  def _findPosition(self, key):
    i = 0
    while (i < self.getNum() and self.getKey(i) < key):
      i += 1
    return i
  
  # insert (key,,value) into nonfull leaf node
  def _insertNonFull(self, leaf, key, value, index):
    if index < 2 * self.t - 1 and leaf.getNum() != 0 and leaf.getKey(index) == key:
      # duplicate key,simply overwrite value
      leaf.setKeyAndData(index, (key, value))
    else:
      # move place to insert key
      for i in range(leaf.getNum(), index, -1):
        leaf.setKeyAndData(i, leaf.getKeyAndData(i-1))
      leaf.setNum(leaf.getNum() + 1)
      leaf.setKeyAndData(index, (key, value))
    
  # return split,key,left,right
  def insert(self, key, value):
    # find the pos to insert
    pos = self._findPosition(key)
    if self.isFull(): # leaf is full,split it
      threshold = self.t
      right = BPlusTreeLeaf(self.tree, self.parent)

      self.setNext(right)
      right.setPrev(self)

      right.setNum(self.getNum() - threshold)
      # copy [t:2t-1] to sibling
      for i in range(0, right.getNum()):
        right.setKeyAndData(i, self.getKeyAndData(threshold+i))
      self.setNum(threshold)
      if pos < threshold:
        # insert to right
        self._insertNonFull(self,key,value,pos)
      else:
        # insert to left
        self._insertNonFull(right,key,value,pos - threshold)
      return True,right.getKey(0),self,right
    else:
      # leaf is not full
      self._insertNonFull(self,key,value,pos)
      return False,INVALID_KEY,None,None

  def search(self, key):
    pos = self._findPosition(key)
    if pos == self.getNum():
      return None
    if self.getKey(pos) == key:
      return self.datas[pos]
    return None

  def removeFromLeaf(self, pos):
    for i in range(pos, self.getNum()):
      self.setKeyAndData(i, self.getKeyAndData(i + 1))
    
    self.setNum(self.getNum() - 1)

  def rebalance(self):
    # first try borrow from prev silbing
    # then  try borrow from next silbing
    # last try merge with sibling
    pass

  def remove(self, key):
    pos = self._findPosition(key)
    if pos == self.getNum() or self.getKey(pos) != key:
      return False

    self.removeFromLeaf(pos)

    # if node has enough keys, return
    if self.isEnough():
      return True

    # rebalance
    self.rebalance()

    return True

  def traverse(self, result):
    for i in range(0, self.getNum()):
      result.append(self.getKey(i))
    return result

class BPlusTree(object):
  def __init__(self,degree):
    assert(degree >= 2)

    self.t = degree
    self.root = BPlusTreeLeaf(self, None)
  
  def insert(self, key, value):
    split,key,left,right = self.root.insert(key,value)

    if not split:
      return
    # if the old root has been split,then create a new root
    root = BPlusTreeNode(self, None)
    root.setNum(1)
    root.setKey(0, key)
    root.setChild(0,left)
    root.setChild(1,right)
    self.root = root

  def search(self, key):
    return self.root.search(key)

  def remove(self, key):
    return self.root.remove(key)

  # traverse a btree, return from left to right leaf's key list
  def traverse(self):
    return self.root.traverse([])

# unit tests for BPlusTree
class BPlusTreeTests(unittest.TestCase):
  def test_additions(self):    
    bt = BPlusTree(20)

    l = []
    inserted = {}
    for i in range(0,5000):
      item = random.randint(1,100000)
      l.append(item)
      bt.insert(item, item)

    # unique insert key
    newList = []
    for i in l:
      if i in inserted:
        continue
      inserted[i] = True
      newList.append(i)
    newList.sort()

    result = bt.traverse()

    self.assertEqual(len(result), len(newList))    
    for i in range(len(result)):
      self.assertEqual(result[i], newList[i])    

  def test_search(self):
    bt = BPlusTree(20)

    l = []
    for i in range(0,5000):
      item = random.randint(1,100000)
      l.append(item)
      bt.insert(item, item)

    result = bt.traverse()

    for i in range(len(result)):
      self.assertEqual(bt.search(l[i]), l[i])   

if __name__ == '__main__':
    unittest.main()

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

  def canBorrow(self):
    return self.num >= self.t

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

  # child must not be the first child
  def changeKey(self, child):
    for i in range(1, self.getNum() + 1):
      if self.getChild(i) != child:
        continue

      key = child.getKey(0)
      self.setKey(i - 1, key)
      break 

  # delete child and its previous key
  def deleteChild(self, child):    
    pos = 0
    # first find the location of child
    for i in range(1, self.getNum() + 1):
      if self.getChild(i) != child:
        continue 
      pos = i
      break
    
    # move key and child one step behind
    for i in range(pos, self.getNum()):
      self.setKey(i - 1,  self.getKey(i))
      self.setChild(i,    self.getChild(i + 1))

    self.setNum(self.getNum() - 1)

  def findPosInParent(self, child):
    parent = self.getParent()
    for i in range(1, parent.getNum() + 1):
      if parent.getChild(i) != child:
        return i - 1

  def borrowFromPrevSibling(self):
    pos = self.findPosInParent(self)
    prev = self.getPrev()

    # move data in self one step ahead
    self.setChild(self.getNum() + 1, self.getChild(self.getNum()))
    for i in range(self.getNum() - 1, -1, -1):
      self.setKeyAndChild(i + 1, self.getKeyAndChild(i))

    # set prev's last child as first child of self
    self.setChild(0, prev.getChild(prev.getNum()))

    prevLastKey = prev.getKey(prev.getNum() - 1)

    # change number of self and prev
    self.setNum(self.getNum() + 1)
    prev.setNum(prev.getNum() - 1)
    
    # update parent key

    # move prev old last key as parent.key[pos]
    key = self.getParent().getKey(pos)
    self.getParent().setKey(pos,prevLastKey)      
    # move the key in parent.key[pos] as first key
    self.setKey(0, key)    

  def borrowFromNextSibling(self):
    next = self.getNext()
    pos = self.findPosInParent(next)    

    # move parent.key[pos] as self last key
    self.setKey(self.getNum(), self.getParent().getKey(pos))
    # move next first child as self last child
    self.setChild(self.getNum() + 1, next.getChild(0))
    # move next first key as parent.key[pos]
    self.getParent().setKey(pos, next.getKey(0))

    # move data in next one step behind
    for i in range(1, next.getNum()):
      next.setKeyAndChild(i - 1, next.getKeyAndChild(i))
    next.setChild(next.getNum() - 1, next.getChild(next.getNum()))

    # change number of self and next
    self.setNum(self.getNum() + 1)
    next.setNum(next.getNum() - 1)

  # merge next to prev and delete next in parent
  def merge(self, prev, next):
    assert(prev.getNext() == next)
    assert(next.getPrev() == prev)
    pos = self.findPosInParent(next) 

    # move parent.key[pos] as prev last key
    prev.setKey(prev.getNum(), self.getParent().getKey(pos))

    # move all next data to prev
    for i in range(next.getNum()):
      prev.setKeyAndChild(prev.getNum() + i + 1, next.getKeyAndChild(i))
      
    prev.setChild(prev.getNum() + next.getNum() + 1, next.getChild(next.getNum()))

    # change number of prev and next
    prev.setNum(prev.getNum() + next.getNum())       
    next.setNum(0)
    prev.setNext(None)
    next.setPrev(None)

    # delete next in parent
    self.getParent().deleteInternal(next)

  def rebalance(self):
    prev = self.getPrev()
    next = self.getNext()

    if prev and prev.canBorrow():   # first try borrow from prev silbing
      self.borrowFromPrevSibling()
    elif next and next.canBorrow(): # then  try borrow from next silbing
      self.borrowFromNextSibling()
    else:                           # last try merge with sibling
      if prev:                      # merge with prev sibling
        self.merge(prev, self)    
      else:                         # merge with next sibling
        self.merge(self, next)

  def deleteInternal(self, child):
    self.deleteChild(child)
   
    if self.isEnough():
      return

    if not self.getParent():  # if is root?
      if self.getNum() == 0:
        self.tree.root = BPlusTreeLeaf(self, None)
      elif self.getNum() == 1 and self.getChild(1) == None:
        pass      
      return

    self.rebalance()
    
  def remove(self, key):
    pos = self._findPosition(key)
    if pos == len(self.children) or self.getChild(pos) == None:
      return False

    return self.getChild(pos).remove(key)

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
    for i in range(pos, self.getNum() - 1):
      self.setKeyAndData(i, self.getKeyAndData(i + 1))
    
    self.setNum(self.getNum() - 1)

  def borrowFromPrevSibling(self):
    prev = self.getPrev()

    # move data in self one step ahead
    for i in range(self.getNum() - 1, -1, -1):
      self.setKeyAndData(i + 1, self.getKeyAndData(i))
    # set prev's last data as first data of self
    self.setKeyAndData(0, prev.getKeyAndData(prev.getNum() - 1))
    # change number of self and prev
    self.setNum(self.getNum() + 1)
    prev.setNum(prev.getNum() - 1)
    # update parent key
    if self.getParent():
      self.getParent().changeKey(self)      

  def borrowFromNextSibling(self):
    next = self.getNext()

    # set next's first data as last data of self
    self.setKeyAndData(self.getNum(), next.getKeyAndData(0))

    # move data in next one step behind
    for i in range(1, next.getNum()):
      next.setKeyAndData(i - 1, next.getKeyAndData(i))

    # change number of self and next
    self.setNum(self.getNum() + 1)
    next.setNum(next.getNum() - 1)
    # update parent key
    if self.getParent():
      self.getParent().changeKey(next)  

  def merge(self, prev, next):
    next = self.getNext()
    prevNum = prev.getNum()

    # move next's data to prev
    for i in range(next.getNum()):
      prev.setKeyAndData(prevNum + i, next.getKeyAndData(i))

    # change number of self and next
    prev.setNum(next.getNum() + prevNum)       
    next.setNum(0)

    prev.setNext(None)
    next.setPrev(None)

    if self.getParent():
      self.getParent.deleteInternal(next)

  def rebalance(self):
    prev = self.getPrev()
    next = self.getNext()

    if prev and prev.canBorrow():   # first try borrow from prev silbing
      self.borrowFromPrevSibling()
    elif next and next.canBorrow(): # then  try borrow from next silbing
      self.borrowFromNextSibling()
    else:                           # last try merge with sibling
      if prev:                      # merge with prev sibling
        self.merge(prev, self)    
      else:                         # merge with next sibling
        self.merge(self, next)   

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

  def test_removals(self):
    bt = BPlusTree(2)
    l = []
    for i in range(0,50):
      item = random.randint(1,100000)
      l.append(item)
      bt.insert(item, item)

    index = random.randint(1,100000) % len(l)
    item = l[index]
    l.pop(index)

    bt.remove(item)

    l.sort()
    result = bt.traverse()
    print 'after remove ', item, ":",l
    print "traverse bt:", result

    for i in range(len(result)):
        self.assertEqual(result[i], l[i])

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

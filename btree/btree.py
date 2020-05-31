# -*- coding: UTF-8 -*-
import random
import unittest

INVALID_KEY = -1

class BTreeNode(object):
  def __init__(self, tree, isLeaf):
    self.num = 0
    self.leaf = isLeaf
    self.tree = tree
    self.t = tree.t
    t = self.t

    self.keys = []
    self.datas = []
    for i in range(2 * t - 1):
      self.keys.append(INVALID_KEY)
      self.datas.append(INVALID_KEY)

    self.children = []    
    for i in range(2 * t):
      self.children.append(None)

  def isLeaf(self):
    return self.leaf

  def getNum(self):
    return self.num

  def setNum(self, num):
    self.num = num

  def setKeyAndData(self, index, packed):
    key, data = packed
    self.keys[index] = key
    self.datas[index] = data

  def getKeyAndData(self, index):
    return self.keys[index],self.datas[index]

  def getKey(self, index):
    return self.keys[index]

  def setChild(self, index, child):
    self.children[index] = child
  
  def getChild(self, index):
    return self.children[index]

  def isFull(self):
    return self.num == 2 * self.t - 1

  # split the child y of this node,y must be full when called
  def splitChild(self, i, y):
    assert(y.isFull())

    t = self.t

    # allocate a new node which is going to store (t-1) keys of y 
    z = type(self)(self.tree, y.isLeaf())
    z.setNum(t - 1)

    # move y.keys[t:2t-1] to z.keys[0:t-1]
    for j in range(0, t - 1):
      z.setKeyAndData(j, y.getKeyAndData(j + t))

    if not y.isLeaf():  # if y is not a leaf
      # move y.children[t:2t] to z.children[0:t]
      for j in range(0, t):
        z.setChild(j, y.getChild(j + t))
        # reset y's moved child 
        #y.setChild(j + t, None)

    # reduce y keys number
    y.setNum(t - 1)
    
    # move child to create space for new child
    for j in range(self.getNum(), i, -1):
      self.setChild(j + 1, self.getChild(j))    
    # insert z to self.children
    self.setChild(i + 1, z)

    # move key to create space for new key
    for j in range(self.getNum() - 1, i - 1, -1):
      self.setKeyAndData(j + 1, self.getKeyAndData(j))
    
    self.setKeyAndData(i,y.getKeyAndData(t - 1))

    # increment the number
    self.setNum(self.getNum() + 1)

  # when called node must be not full
  def insertNonFull(self, key, data):
    i = self.getNum() - 1

    if self.isLeaf(): # if is leaf
      # 1.find the location of the new key
      # 2.move all greater keys to one place ahead
      while i >= 0 and (self.getKey(i) == INVALID_KEY or self.getKey(i) > key):
        self.setKeyAndData(i + 1, self.getKeyAndData(i))
        i -= 1
      # insert new key
      self.setKeyAndData(i + 1, (key, data))
      self.setNum(self.getNum() + 1)
    else:             # if is internal node
      # find the location of the new key
      while i >= 0 and (self.getKey(i) == INVALID_KEY or self.getKey(i) > key):
        i -= 1      
      
      # if the child is full,split it
      y = self.getChild(i + 1)
      if y.isFull():
        self.splitChild(i + 1, y)
        if self.getKey(i + 1) < key:
          i += 1
      self.getChild(i + 1).insertNonFull(key, data)
  
  # find the location of the key, return index and found
  def _findKey(self, key):
    i = 0
    while (i < self.getNum() and self.getKey(i) < key):
      i += 1
    return i, i < self.getNum() and self.getKey(i) == key

  # remove the idx-th key from this node,which is a leaf
  def _removeFromLeaf(self, idx):
    for i in range(idx + 1, self.getNum()):
      self.setKeyAndData(i - 1, self.getKeyAndData(i))
    self.setNum(self.getNum() - 1)
  
  # remove the idx-th key from this node,which is a internal node
  def _removeFromNode(self, idx):
    key = self.getKey(idx)

    if self.getChild(idx).getNum() >= self.t:
      # If the child that precedes k (C[idx]) has atleast t keys, 
      # find the predecessor 'pred' of k in the subtree rooted at 
      # C[idx]. Replace k by pred. Recursively delete pred 
      # in C[idx]       
      pred,data = self._getPred(idx)
      self.setKeyAndData(idx, (pred, data))
      self.getChild(idx).remove(pred)   
    elif self.getChild(idx + 1).getNum() >= self.t:
      # If the child C[idx] has less that t keys, examine C[idx+1]. 
      # If C[idx+1] has atleast t keys, find the successor 'succ' of k in 
      # the subtree rooted at C[idx+1] 
      # Replace k by succ 
      # Recursively delete succ in C[idx+1]          
      succ,data = self._getSucc(idx)
      self.setKeyAndData(idx, (succ, data))
      self.getChild(idx + 1).remove(succ)
    else:
      # If both C[idx] and C[idx+1] has less that t keys,merge k and all of C[idx+1] 
      # into C[idx] 
      # Now C[idx] contains 2t-1 keys 
      # Free C[idx+1] and recursively delete k from C[idx]    
      self._merge(idx)
      self.getChild(idx).remove(key)
  
  # merge C[idx] with C[idx+1] 
  # C[idx+1] is freed after merging   
  def _merge(self, idx):
    t = self.t
    child = self.getChild(idx)
    sibling = self.getChild(idx+1)

    # Pulling a key from the current node and inserting it into (t-1)th 
    # position of C[idx] 
    child.setKeyAndData(t - 1, self.getKeyAndData(idx))

    # Copying the keys from C[idx+1] to C[idx] at the end 
    for i in range(0, sibling.getNum()):
      child.setKeyAndData(i + t, sibling.getKeyAndData(i))
    
    # Copying the child pointers from C[idx+1] to C[idx] 
    if not child.isLeaf():
      for i in range(0, sibling.getNum() + 1):
        child.setChild(i + t, sibling.getChild(i))
    
    # Moving all keys after idx in the current node one step before - 
    # to fill the gap created by moving keys[idx] to C[idx]     
    for i in range(idx + 1, self.getNum()):
      self.setKeyAndData(i - 1, self.getKeyAndData(i))

    # Moving the child pointers after (idx+1) in the current node one 
    # step before 
    for i in range(idx + 2, self.getNum() + 1):
      self.setChild(i - 1, self.getChild(i))
    
    # Updating the key count of child and the current node 
    child.setNum(child.getNum() + sibling.getNum() + 1)
    self.setNum(self.getNum() - 1)

  # get predecessor of keys[idx] 
  def _getPred(self, idx):
    # Keep moving to the right most node until we reach a leaf
    cur = self.getChild(idx)
    while not cur.isLeaf():
      cur = cur.getChild(cur.getNum())
    
    # Return the last key of the leaf
    return cur.getKeyAndData(cur.getNum() - 1)

  # get successor of keys[idx] 
  def _getSucc(self, idx):
    # Keep moving the left most node starting from C[idx+1] until we reach a leaf
    cur = self.getChild(idx + 1)
    while not cur.isLeaf():
      cur = cur.getChild(0)
    
    # Return the first key of the leaf
    return cur.getKeyAndData(0)

  def _fill(self, idx):
    t = self.t
    if idx != 0 and self.getChild(idx - 1).getNum() >= t:
      # If the previous child(C[idx-1]) has more than t-1 keys, borrow a key 
      # from that child
      self._borrowFromPrev(idx)
    if idx != self.getNum() and self.getChild(idx + 1).getNum() >= t:
      # If the next child(C[idx+1]) has more than t-1 keys, borrow a key 
      # from that child
      self._borrowFromNext(idx)
    else:
      # Merge C[idx] with its sibling 
      # If C[idx] is the last child, merge it with with its previous sibling 
      # Otherwise merge it with its next sibling
      if idx != self.getNum():
        self._merge(idx)
      else:
        self._merge(idx - 1)

  # borrow a key from C[idx-1] and insert it into C[idx] 
  def _borrowFromPrev(self, idx):
    child = self.getChild(idx)
    sibling = self.getChild(idx - 1)

    # The last key from C[idx-1] goes up to the parent and key[idx-1] 
    # from parent is inserted as the first key in C[idx]. Thus, the loses 
    # sibling one key and child gains one key 

    # Moving all key in C[idx] one step ahead 
    for i in range(child.getNum() - 1, -1, -1):
      child.setKeyAndData(i + 1, child.getKeyAndData(i))
    
    # If C[idx] is not a leaf, move all its child pointers one step ahead 
    if not child.isLeaf():
      for i in range(child.getNum(), -1, -1):
        child.setChild(i + 1, child.getChild(i))   

    # Setting child's first key equal to keys[idx-1] from the current node 
    child.setKeyAndData(0, self.getKeyAndData(idx - 1))

    # Moving sibling's last child as C[idx]'s first child 
    if not child.isLeaf():
      child.setChild(0, sibling.getChild(sibling.getNum())) 

    # Moving the key from the sibling to the parent 
    # This reduces the number of keys in the sibling 
    self.setKeyAndData(idx - 1, sibling.getKeyAndData(sibling.getNum() - 1))

    child.setNum(child.getNum() + 1)
    sibling.setNum(sibling.getNum() - 1)

  # borrow a key from the C[idx+1] and place it in C[idx]  
  def _borrowFromNext(self, idx):
    child = self.getChild(idx)
    sibling = self.getChild(idx + 1)

    # keys[idx] is inserted as the last key in C[idx] 
    child.setKeyAndData(child.getNum(), self.getKeyAndData(idx))
    
    # Sibling's first child is inserted as the last child into C[idx]
    if not child.isLeaf():
      child.setChild(child.getNum() + 1, sibling.getChild(0)) 

    # The first key from sibling is inserted into keys[idx] 
    self.setKeyAndData(idx, sibling.getKeyAndData(0))

    # Moving all keys in sibling one step behind 
    for i in range(1, sibling.getNum()):
      sibling.setKeyAndData(i - 1, sibling.getKeyAndData(i))
 
    # Moving the child pointers one step behind 
    if not sibling.isLeaf():
      for i in range(1, sibling.getNum() + 1):
        sibling.setChild(i - 1, sibling.setChild(i))  
    
    # Increasing and decreasing the key count of C[idx] and C[idx+1] respectively 
    child.setNum(child.getNum() + 1)
    sibling.setNum(sibling.getNum() - 1)

  def remove(self, key):
    i,found = self._findKey(key)

    if found: # if key present in this node
      if self.isLeaf():
        self._removeFromLeaf(i)
      else:
        self._removeFromNode(i)
      return True
    else:
      # if node is leaf and key not present in it,return False
      if self.isLeaf():
        return False

      # The key to be removed is present in the sub-tree rooted with this node 
      # The flag indicates whether the key is present in the sub-tree rooted 
      # with the last child of this node
      flag = False
      if i == self.getNum():
        flag = True

      # If the child where the key is supposed to exist has less that t keys, 
      # we fill that child 
      if self.getChild(i).getNum() < self.t:
        self._fill(i)
      
      # If the last child has been merged, it must have merged with the previous 
      # child and so we recurse on the (idx-1)th child. Else, we recurse on the 
      # (idx)th child which now has atleast t keys 
      if flag and i > self.getNum():
        return self.getChild(i - 1).remove(key)
      else:
        return self.getChild(i).remove(key)

  def search(self, key):
    i,found = self._findKey(key)

    if found: # if key present in this node
      return self.datas[i]

    if self.isLeaf(): # if key not present in this node and is a leaf
      return None
    # else search key in child
    return self.getChild(i).search(key)

  def traverse(self, result):
    # iterate over all keys
    for i in range(self.getNum()):
      if not self.isLeaf():
        result = self.getChild(i).traverse(result)
      result.append(self.getKey(i))

    if not self.isLeaf():
        result = self.getChild(self.getNum()).traverse(result)
    
    return result

  def printDebug(self):
    print 'num:', self.getNum()
    msg = "keys(" + str(self.isLeaf()) + "):"
    for i in range(self.getNum()):
      key = self.getKey(i)
      msg += str(key) + ","
    print msg[:-1]
    
    for i in range(self.getNum() + 1):
      child = self.children[i]
      if not child:
        continue
      print "children[", i, "]:"
      child.printDebug()
    pass

class BTree(object):
  NODE = LEAD = BTreeNode

  def __init__(self, degree):
    self.t = degree
    self.root = None

  def _isEmpty(self):
    return self.root == None

  def insert(self, key, data):
    if self._isEmpty(): # if tree is empty 
      root = self.NODE(self, True)
      root.setKeyAndData(0, (key, data))
      root.setNum(1)
      self.root = root
    else:             # if tree is not empty
      root = self.root

      if root.isFull():  # if root is full,then grows in height
        # allocate a new internal node
        s = self.NODE(self, False)
        
        # make old root as the first child of new root
        s.setChild(0, root)

        # split the old root and move 1 key to the new root
        s.splitChild(0, root)

        # now the new root is not full,insert the key
        i = 0
        if s.getKey(0) != INVALID_KEY and s.getKey(0) < key:
          i = 1

        s.getChild(i).insertNonFull(key, data)

        # change root
        self.root = s
      else:        
        # if root is not full,call insertNonFull for root
        root.insertNonFull(key, data)
  
  # remove the key,return True or False
  def remove(self, key):
    if self._isEmpty():
      return False
    
    ret = self.root.remove(key)
    # if the root is empty,make the first child as new root
    if ret and self.root.getNum() == 0:
      if self.root.isLeaf():
        self.root = None
      else:
        self.root = self.root.getChild(0)

    return ret

  def search(self, key):
    if self._isEmpty(): # if btree is empty
      return None
    return self.root.search(key)

  def printDebug(self):
    self.root.printDebug()
    print "\n\n"

  def _checkNode(self, node, parent_key):
    if parent_key and not (node.getNum() >= self.t - 1 and node.getNum() <= self.t * 2 - 1):
      return False

    children = node.children
    keys = node.keys

    # check keys
    lastkey = INVALID_KEY
    for i in range(node.getNum()):
      key = keys[i]

      if key < lastkey:
        return False
      lastkey = key 

    # check children
    for i in range(node.getNum() + 1):
      child = children[i]
      if not child:
        continue

      key = None
      if i != len(children) - 1:
        key = keys[i]

      if child.isLeaf():
        ret = self._checkLeaf(child, key)
      else:
        ret = self._checkNode(child, key)

      if not ret:
        return False

    return True

  def _checkLeaf(self, leaf, parent_key):
    keys = leaf.keys
    # check keys
    lastkey = INVALID_KEY
    for i in range(leaf.getNum()):
      key = keys[i]

      if key < lastkey:
        return False
      lastkey = key    
  
    return True

  # check btree attributes recursively
  def checkAttr(self):
    if self._isEmpty():
      return True

    root = self.root
    if root.isLeaf():
      return self._checkLeaf(root, None)
    else:
      return self._checkNode(root, None)
  
  # traverse a btree, return mid-order traverse list
  def traverse(self):
    if self._isEmpty():
      return []
    return self.root.traverse([])

# unit tests for BTree
class BTreeTests(unittest.TestCase):
  def test_additions(self):    
    bt = BTree(20)
    l = []
    for i in range(0,1000):
      item = random.randint(1,100000)
      l.append(item)
      bt.insert(item, item)

    self.assertTrue(bt.checkAttr())

    result = bt.traverse()
    l.sort()

    for i in range(len(result)):
        self.assertEqual(result[i], l[i])

  def test_removals(self):
    bt = BTree(20)
    l = []
    for i in range(0,1000):
      item = random.randint(1,100000)
      l.append(item)
      bt.insert(item, item)

    index = random.randint(1,100000) % len(l)
    item = l[index]
    l.pop(index)
    bt.remove(item)
    
    self.assertTrue(bt.checkAttr())

    l.sort()
    result = bt.traverse()
    for i in range(len(result)):
        self.assertEqual(result[i], l[i])
  
  def test_search(self):
    bt = BTree(20)
    l = []
    for i in range(0,1000):
      item = random.randint(1,100000)
      l.append(item)
      bt.insert(item, item)
    
    index = random.randint(1,100000) % len(l)
    item = l[index]

    ret = bt.search(item)
    self.assertTrue(ret != None)
    self.assertEqual(ret,item)

if __name__ == '__main__':
    unittest.main()


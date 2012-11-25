import sqlite3
import time
import bisect
import difflib
import logging
import random
import os, shutil

class Item:
  timelimit = 4
  max_score = 10

  def __init__(self, row, last_score):
    self.__timer = time.time()
    self.__row = row
    self.__last_score = last_score

  def forward(self):
    return self.__last_score < Item.max_score/2

  # heuristically assign the memory
  def done(self, db, correct=True):
    _time = int(time.time() - self.__timer)
    self.__timer = 0

    score = 0

    # Scoring:
    #  forward < timelimit: max/2
    #  forward < timelimit*2: max/4
    #  forward < timelimit*2: max/4
    #  reverse < timelimit: max
    #  wrong_answer: last_score/2
    if not correct:
      score = self.last_score()/2
    else:
      if _time < Item.timelimit:
        score = Item.max_score
      elif _time < Item.timelimit*2:
        score = Item.max_score/2
      else:
        score = Item.max_score/4
      if self.forward():
        score /= 2

    logging.debug("Setting ato of %s to %d [time=%d]", self, score, _time)

    db.save(self, score)

  def last_score(self):
    return self.__last_score

  def tags(self):
    return self.__row['tags']

  def question(self):
    if self.forward():
      return self.__row['key']
    else:
      return self.__row['value']

  def answer(self):
    if self.forward():
      return self.__row['value']
    else:
      return self.__row['key']

  def id(self):
    return self.__row['id']

  def __str__(self):
    return "Item<id=%s question=%s>" % (self.__row['id'], self.question())

class DB:
  question_limit_choice = 20
  uid = 0 # single user for now
  n_unseen_questions = """
    SELECT id,difficulty
      FROM dictionary
      WHERE id IN (
        SELECT id
          FROM dictionary
        EXCEPT
        SELECT dict_id
          FROM scores
          WHERE uid=?)
      ORDER BY difficulty
      LIMIT {unseen_question_limit}
      """.format(unseen_question_limit=question_limit_choice/2)

  n_seen_questions = """
    SELECT id,difficulty
      FROM dictionary
      WHERE id IN (
        SELECT dict_id
          FROM scores
          WHERE uid=? AND
          (
            (score >= {decent_score} AND
             last_updated < DATETIME('now','-1 month')) OR
            (score BETWEEN {decent_score} AND {low_score} AND
             last_updated < DATETIME('now','-1 day')) OR
            (score <= {low_score} AND
             last_updated < DATETIME('now','-10 minutes'))))
      ORDER BY difficulty
      LIMIT {seen_question_limit}
      """.format(
          decent_score=Item.max_score*3/4,
          low_score=Item.max_score/4,
          seen_question_limit=question_limit_choice/2)

  question = "SELECT * FROM dictionary WHERE id = ?"
  score = "SELECT * FROM scores WHERE dict_id = ? AND uid = ?"
  update_score = """
    UPDATE scores
    SET
      score = :score,
      last_updated = DATETIME('now')
    WHERE
      dict_id = :dict_id AND uid = :uid
  """
  insert_score = """
    INSERT INTO scores
    VALUES (
      :uid,
      DATETIME('now'),
      :dict_id,
      :score)
  """
  update_history = """
    INSERT INTO history (uid, time, score)
      SELECT uid,DATETIME('now'),SUM(score)
        FROM scores
        GROUP BY uid
  """
  insert_questions = """
    INSERT INTO dictionary
      VALUES (NULL, :difficulty, :key, :value, :tag)
  """

  def open(self, fname):
    logging.debug("Loading from %s", fname)
    is_new = not os.path.exists(fname)
    self.conn = sqlite3.connect(fname)
    self.conn.row_factory = sqlite3.Row
    if is_new:
      self.init(fname)

  def close(self):
    c = self.conn.cursor()
    c.execute(DB.update_history)
    self.conn.commit()
    self.conn.close()

  def save(self, item, score):
    c = self.conn.cursor()
    c.execute(DB.score, (item.id(), DB.uid))
    score_row = c.fetchone()
    data = {
        'uid': DB.uid,
        'dict_id': item.id(),
        'score': score,
        }
    if score_row:
      logging.debug("Updating: %s", item)
      c.execute(DB.update_score, data)
    else:
      logging.debug("Inserting: %s", item)
      c.execute(DB.insert_score, data)
    self.conn.commit()

  def getNextItem(self):
    c = self.conn.cursor()
    ids = []
    c.execute(DB.n_unseen_questions, (DB.uid,))
    for r in c:
      ids.append(r['id'])
    c.execute(DB.n_seen_questions, (DB.uid,))
    for r in c:
      ids.append(r['id'])
    logging.debug("Fetched %d questions", len(ids))

    dict_id = ids[random.randrange(len(ids))]
    c.execute(DB.question, (dict_id, ))
    row = c.fetchone()
    assert row is not None, "dict_id: %s didnt return any rows" % (dict_id)
    c.execute(DB.score, (dict_id, DB.uid))
    score_row = c.fetchone()
    last_score = 0
    if score_row:
      last_score = score_row['score']
    return Item(row, last_score)

  def init(self, fname):
    path = os.path.dirname(__file__)
    with open(os.path.join(path, 'schema.sql'), 'r') as f:
      schema = f.read()
      self.conn.executescript(schema)
    self.load('basic', os.path.join(path, 'kannada.db'))

  def load(self, tag, fname):
    c = self.conn.cursor()
    with open(fname, 'r') as f:
      for entry in f.readlines():
        items = entry.split('|')
        assert len(items) == 3, "Expected difficulty[0-2]|question|answer. Got: %s" % entry
        data = {
          'key':        items[1],
          'value':      items[2],
          'difficulty': items[0],
          'tag':        tag,
          }
        logging.debug("Inserting: %s", data)
        c.execute(DB.insert_questions, data)
    self.conn.commit()

if __name__ == '__main__':
  import sys
  db = DB()
  db.open(sys.argv[1])
  db.load(sys.argv[2], sys.argv[3])
  db.close()

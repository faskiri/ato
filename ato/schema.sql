CREATE TABLE dictionary
(
  id            INTEGER PRIMARY KEY ASC,
  difficulty    INTEGER,
  key           STRING,
  value         STRING,
  tag           STRING
);

CREATE TABLE scores
(
  uid           INTEGER,
  last_updated  TIMESTAMP,
  dict_id       INTEGER,
  score         INTEGER,
  FOREIGN KEY(dict_id) REFERENCES dictionary(id)
);

CREATE TABLE history
(
  uid           INTEGER,
  time          DATETIME,
  score         INTEGER
);

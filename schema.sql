drop table if exists posts;
create table posts (
  id integer primary key autoincrement,
  title text not null,
  'text' text not null,
  media text -- link or path to media / photo gallery
);
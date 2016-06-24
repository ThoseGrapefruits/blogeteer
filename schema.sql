drop table if exists posts;
drop table if exists users;

create table entries (
  id integer primary key autoincrement,
  title text not null,
  author integer not null,
  'text' text not null,
  media text, -- link or path to media / photo gallery
  foreign key(author) references users(id)
);

create table users (
  id integer primary key autoincrement,
  username text not null,
  fullname text,
  bio text
);
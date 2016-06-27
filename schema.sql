drop table if exists users;
drop table if exists entries;
drop table if exists media;

create table users (
  id       integer primary key autoincrement,
  username text not null,
  email    text not null,
  passhash text not null,
  fullname text,
  bio      text
);

create table entries (
  id      integer primary key autoincrement,
  title   text not null,
  author  integer not null,
  body text not null,
  media   text, -- link or path to media / photo gallery
  foreign key (author) references users(id)
);

create table media (
  id       integer primary key autoincrement,
  date     integer not null,
  savedir  text    not null,
  filename text    not null,
  owner    integer not null,
  parent   integer, -- null for uploaded media, references parent for thumbnails
  xLen     integer not null,
  yLen     integer not null,
  foreign key (owner) references users (id),
  foreign key (parent) references media (id)
)
drop table if exists entries;
drop table if exists users;

create table entries (
  id      integer primary key autoincrement,
  title   text    not null,

  author  integer not null,
          foreign key (author) references users (id),

  content text    not null,
  media   text -- link or path to media / photo gallery
);

create table users (
  id       integer primary key autoincrement,
  username text not null,
  email    text not null,
  passhash text not null,
  fullname text,
  bio      text
);

create table media (
  id       integer primary key autoincrement,
  date     integer not null,
  savedir  text    not null,
  filename text    not null,

  owner    integer not null,
           foreign key (owner) references users (id),

  parent   integer, -- null for uploaded media, references parent for thumbnails
           foreign key (parent) references media (id),

  xLen     integer not null,
  yLen     integer not null
)
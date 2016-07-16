drop table if exists users;
drop table if exists entries;
drop table if exists media;
drop table if exists user_temp;

create table users (
  username text primary key,
  email    text not null,
  passhash text not null,
  fullname text,
  bio      text
);

create table entries (
  slug      text primary key,
  title     text not null,
  author    text not null,
  body      text not null,
  media     text, -- link or path to media / photo gallery
  date_time datetime default current_timestamp,
  foreign key (author) references users (username)
);

create table media (
  id       integer primary key autoincrement,
  date     integer not null,
  savedir  text    not null,
  filename text    not null,
  owner    text    not null,
  parent   integer, -- null for uploaded media, references parent for thumbnails
  x_len     integer not null,
  y_len     integer not null,
  foreign key (owner) references users (username),
  foreign key (parent) references media (id)
);

create table user_temp (
  username    text primare key,
  temp_key    text not null,
  destination text not null
);
drop table if exists users;
drop table if exists entries;
drop table if exists media;
drop table if exists user_temp;

create table users (
  username text primary key,
  email    text not null,
  passhash text not null,
  fullname text,
  bio      text,
  creation_date datetime default current_timestamp
);

create table entries (
  id        integer primary key autoincrement,
  slug      text unique,
  title     text ,
  author    text not null,
  body      text,
  media     text, -- optional link or path to media / photo gallery
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
  username    text primary key,
  temp_key    text not null,
  destination text not null
);

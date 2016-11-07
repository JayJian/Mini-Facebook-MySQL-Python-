CREATE DATABASE photoshare;
USE photoshare;
DROP TABLE Pictures CASCADE;
DROP TABLE Users CASCADE;

CREATE TABLE Users (
  user_id int4  AUTO_INCREMENT,
  first_name VARCHAR(35),
  last_name VARCHAR(35),
  email varchar(255) UNIQUE,
  password varchar(255),
  hometown VARCHAR(255),
  birthday DATE,
  CONSTRAINT users_pk PRIMARY KEY (user_id)
);

CREATE TABLE Albums
(
  album_id int4 AUTO_INCREMENT,
  album_name VARCHAR(70) NOT NULL,
  updated_time TIMESTAMP,
  buser_id int4 NOT NULL,
  PRIMARY KEY (album_id),
  FOREIGN KEY (buser_id) REFERENCES Users(user_id)
);


CREATE TABLE Pictures
(
  picture_id int4  AUTO_INCREMENT,
  user_id int4,
  imgdata longblob ,
  caption VARCHAR(255),
  album_id int4 NOT NULL,
  INDEX upid_idx (user_id),
  CONSTRAINT pictures_pk PRIMARY KEY (picture_id),
  FOREIGN KEY (album_id) REFERENCES Albums(album_id)
);

CREATE TABLE Acts (
  actId int4 AUTO_INCREMENT,
  user_id int4 NOT NULL,
  PRIMARY KEY (actId),
  FOREIGN KEY (user_id) REFERENCES Users(user_id)
);

CREATE TABLE Comments
(
  com_id int4 AUTO_INCREMENT,
  picture_id int4 NOT NULL,
  content VARCHAR(512) NOT NULL,
  email VARCHAR(255),
  updated_time TIMESTAMP,
  PRIMARY KEY (com_id)
);


CREATE TABLE Tags
(
  tag_id int4 AUTO_INCREMENT,
  tag_string VARCHAR(35),
  picture_id int4 NOT NULL,
  PRIMARY KEY (tag_id),
  FOREIGN KEY (picture_id) REFERENCES Pictures(picture_id)
);

CREATE TABLE Friends
(
  user1_id int4 NOT NULL,
  user2_id int4 NOT NULL,
  PRIMARY KEY (user1_id, user2_id),
  FOREIGN KEY (user1_id) REFERENCES Users(user_id),
  FOREIGN KEY (user2_id) REFERENCES Users(user_id)
);


CREATE TABLE likes
(
  picture_id int4 NOT NULL,
  user_id int4 NOT NULL,
  FOREIGN KEY (picture_id) REFERENCES Pictures(picture_id)
);



INSERT INTO Users (email, password) VALUES ('test@bu.edu', 'test');
INSERT INTO Users (email, password) VALUES ('test1@bu.edu', 'test');

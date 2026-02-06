import 'dart:io';

class UserSession {
  static final UserSession _instance = UserSession._internal();

  factory UserSession() {
    return _instance;
  }

  UserSession._internal();

  String name = "Guest";
  String email = "";
  bool isParent = false;
  String disability = "None";
  File? profileImage;

  void setUser({
    required String name,
    required String email,
    required bool isParent,
    required String disability,
    File? profileImage,
  }) {
    this.name = name;
    this.email = email;
    this.isParent = isParent;
    this.disability = disability;
    this.profileImage = profileImage;
  }

  void clear() {
    name = "Guest";
    email = "";
    isParent = false;
    disability = "None";
    profileImage = null;
  }
}

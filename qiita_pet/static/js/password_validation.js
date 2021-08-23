function validatePasswordIsASCIIOnly(value) {
  if(value.match(/^[\x20-\x7E]{1,}$/)) {
      return true;
  }
  return false;
}

// http://www.9lessons.info/2012/04/bootstrap-registration-form-tutorial.html
function dualpass_validator() {
  // Popover
  $('.dualpass input').hover(function()
  {
    $(this).popover('show');
  });

  jQuery.validator.addMethod("validate_password_is_ascii", validatePasswordIsASCIIOnly,
                             "Passwords may only include printable ASCII characters; e.g., A-Z, a-z, 0-9, space, _, -, @, etc.");

  // Validation
  $(".dualpass").validate({
    rules:{
      username:{required:true,email: true},
      email:{required:true, email: true},
      oldpass:{required:true},
      newpass:{required:true, validate_password_is_ascii:'sel', minlength: 8},
      newpass2:{required:true, validate_password_is_ascii:'sel', equalTo: "#newpass", minlength: 8},
    },

    messages:{
      email:{
        required:"Enter your email address",
        email:"Enter a valid email address"},
      oldpass:{
        required:"Enter your current password"},
      newpass:{
        required:"Enter your new password",
        minlength:"Password must be a minimum of 8 characters"},
      newpass2:{
        required:"Enter your new password again",
        minlength:"Password must be a minimum of 8 characters",
        equalTo:"'Password' and 'Confirm Password' fields must match"}
    }
  });
}

// http://www.9lessons.info/2012/04/bootstrap-registration-form-tutorial.html
function validator_change_password() {
  // Popover
  $('.dualpass input').hover(function()
  {
    $(this).popover('show');
  });

  jQuery.validator.addMethod("validate_password_is_ascii", validatePasswordIsASCIIOnly,
                             "Passwords may only include printable ASCII characters; e.g., A-Z, a-z, 0-9, space, _, -, @, etc.");

  // Validation
  $(".change_password").validate({
    rules:{
      oldpass:{required:true, minlength: 8},
      newpass:{required:true, validate_password_is_ascii:'sel', minlength: 8},
      newpass2:{required:true, validate_password_is_ascii:'sel', equalTo: "#newpass", minlength: 8},
    },

    messages:{
      oldpass:{
        required:"Enter your current password"},
      newpass:{
        required:"Enter your new password",
        minlength:"Password must be a minimum of 8 characters"},
      newpass2:{
        required:"Enter your new password again",
        minlength:"Password must be a minimum of 8 characters",
        equalTo:"'Password' and 'Confirm Password' fields must match"}
    }
  });
}

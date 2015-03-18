// http://www.9lessons.info/2012/04/bootstrap-registration-form-tutorial.html
function dualpass_validator() {
  // Popover 
  $('.dualpass input').hover(function()
  {
    $(this).popover('show');
  });

  // Validation
  $(".dualpass").validate({
    rules:{
      username:{required:true,email: true},
      email:{required:true, email: true},
      oldpass:{required:true},
      newpass:{required:true,minlength: 8},
      newpass2:{required:true,minlength: 8,equalTo: "#newpass"},
    },

    messages:{
      email:{
        required:"Enter your email address",
        email:"Enter valid email address"},
      oldpass:{
        required:"Enter your old password"},
      newpass:{
        required:"Enter your password",
        minlength:"Password must be minimum 8 characters"},
      newpass2:{
        required:"Enter password again",
        minlength:"Password must be minimum 8 characters",
        equalTo:"Password and Confirm Password must match"}
    }
  });
}

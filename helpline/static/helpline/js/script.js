// JavaScript Document
// Get current login duration.
// Interval set to every one second.

$(document).ready(function(){
 setInterval(function () {
           $("#wai").load("leta/");
           $("#sms-notify-badge").load("/messaging/ajax/sms/count");
         }, 1000);

 setInterval(function () {
         $.get("/helpline/call/check/",function(data){
			 if(data.my_case){
                window.location = "/helpline/forms/call/?case="+data.my_case;
		clearInterval(getForm);  
		}
			 });
         }, 1000);

  }); 

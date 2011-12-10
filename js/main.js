$(document).ready(function(){
    $.routes({
        '/': function(){
            load_section("home.html", "home");
        },
        '/home': function(){
            load_section("home.html", "home");
        },
        '/downloads': function(params){
            load_section("downloads.html", "downloads");
        },
        '/bugreport': function(){
            load_section("bugreport.html", "bugreport");
        },
        '/contact': function(){
            load_section("contact.html", "contact");
        }
    });
});

function load_section(document_name, menuitem){
    $.ajax({
        url: document_name,
        dataType: "html",
        cache: false,
        success: function(data){
            $("#content").html(data);
        }
    });

    $("#menubar li a").each(function(index, item){
        if(item.id == menuitem){
            item.className = "selected";
        } else {
            item.className = "";
        }
    });

}

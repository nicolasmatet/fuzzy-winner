

//<!--AJAX for file form submit-->
//    $('#deletion_form').on('submit', function(event){
//        event.preventDefault();
//        console.log("form submitted!")  // sanity check
//        delete_file();
//    });
//
//
//
//    function delete_file() {
//
//        console.log("delete_file is working!") // sanity check
//        var frm = $('#deletion_form');
//
//        $.ajax({
//            url : "/polls/delete_file/", // the endpoint
//            type : "POST", // http method
//            data : { to_be_deleted : frm.serialize()}, // data sent with the post request
//
//            // handle a successful response
//            success : function(json) {
//                $('#deletion_form').val(''); // remove the value from the input
//                console.log(json); // log the returned json to the console
//                console.log("success"); // another sanity check
//            },
//
//            // handle a non-successful response
//            error : function(xhr,errmsg,err) {
//                $('#results').html("<div class='alert-box alert radius' data-alert>Oops! We have encountered an error: "+errmsg+
//                    " <a href='#' class='close'>&times;</a></div>"); // add the error to the dom
//                console.log(xhr.status + ": " + xhr.responseText); // provide a bit more info about the error to the console
//            }
//        });
//    };
//

<!--interaction with the graph-->
    function showDetail() {
       document.getElementById('welcomeDiv').style.display = "block";
    }



    function onoff(node,all_nodes,all_edges,svg,svgiframe) {

/*
            node.addEventListener('click', function(e){
                  var div = document.createElement('div');
                  div.className = 'detailPane';
                   div.style.backgroundColor = "red";
                   div.style.position = "absolute";
                   div.style.width = "100px";
                   div.style.height="100px";
                   //div.style.zIndex = "100";
                   parent = document.getElementsByTagName('body')[0];

                    var pos = node.getBoundingClientRect();
                    var posRef = svgiframe.getBoundingClientRect();
                   div.style.left = posRef.left + pos.left+'px';
                   div.style.top = posRef.top+pos.top+'px';
                  parent.appendChild(div);
             });
*/

            node.addEventListener('mouseover', function(e) {

            //hide the nodes and edges
                var allelmnb = all_nodes.length;
                for (var i = 0; i < allelmnb; i++) {
                    all_nodes[i].style.opacity = "0.05";
                    //all_node[i].className =  all_node[i].className.replace(new RegExp('(?:^|\\s)'+ 'activated' + '(?:\\s|$)'), ' ');
                    //all_node[i].className += ' ' + 'desactivated'
               }
                var allelmnb = all_edges.length;
                for (var i = 0; i < allelmnb; i++) {
                    //all_edges[i].className = "desactivated";
                    all_edges[i].style.opacity = "0.05";
                }


                node.style.fill = '#f50';
                node.style.opacity = "1";

            //display the slaves and the link to them
                var slaves = slave_dictionnary[node.id];
                var arrayLength = slaves.length;
                for (var i = 0; i < arrayLength; i++) {
                    var node_voisin = svg.getElementById(slaves[i]);
                    var link_edge = svg.getElementById(node.id.concat('->',slaves[i]));
                    node_voisin.style.fill = '#f20';
                    node_voisin.style.opacity = "1";
                    link_edge.style.opacity = "1";

                }

                var masters = master_dictionnary[node.id]
                var arrayLength = masters.length;
                for (master in masters) {
                    var node_voisin = svg.getElementById(master);
                    var link_edge = svg.getElementById(master.concat('->',node.id));
                    node_voisin.style.fill = '#f90';
                    node_voisin.style.opacity = "1";
                    link_edge.style.opacity = "1";

                }

           });

           node.addEventListener('mouseout', function(e) {
                var allelmnb = all_nodes.length;
                for (var i = 0; i < allelmnb; i++) {
                    //all_node[i].className =  all_node[i].className.replace(new RegExp('(?:^|\\s)'+ 'desactivated' + '(?:\\s|$)'), ' ');
                    //all_node[i].className += ' ' + 'activated'
                    all_nodes[i].style.opacity = "1";
                    all_nodes[i].style.fill = "";
                }
                var allelmnb = all_edges.length;
                for (var i = 0; i < allelmnb; i++) {
                    all_edges[i].style.opacity = "1";
                    //all_edges[i].className = "activated";
                }

           });
       }

    window.addEventListener('load', function(e) {
        var doc = document.querySelector('#svgiframe'),
           svg = doc.contentDocument || doc.getSVGDocument(),
           nodes = svg.querySelectorAll('.node'),
           edges = svg.querySelectorAll('.edge'),
           i;
       for (i = 0; i < nodes.length; ++i) {
           onoff(nodes[i],nodes,edges,svg,doc);
       }


   });
//

<!--get the csrf token from cookies-->
function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
var csrftoken = getCookie('csrftoken');

<!--add the csrf token to the header of ajax request-->
function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}
$.ajaxSetup({
    beforeSend: function(xhr, settings) {
        if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
        }
    }
});


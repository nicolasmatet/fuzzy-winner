

<!--interaction with the graph-->
    function showDetail() {
       document.getElementById('welcomeDiv').style.display = "block";
    }



    function onoff(node,all_nodes,all_edges,svg,svgiframe) {


            node.addEventListener('mouseover', function(e) {

            //hide the nodes and edges
                var allelmnb = all_nodes.length;
                for (var i = 0; i < allelmnb; i++) {
                    all_nodes[i].style.opacity = "0.05";
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
                    all_nodes[i].style.opacity = "1";
                    all_nodes[i].style.fill = "";
                }
                var allelmnb = all_edges.length;
                for (var i = 0; i < allelmnb; i++) {
                    all_edges[i].style.opacity = "1";
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


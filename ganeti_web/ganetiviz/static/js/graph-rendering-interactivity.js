/*
(c) OSU | Open Source Lab, Pranjal Mittal

This file includes code for rendering of Ganetiviz Graph and Interactivity.
All events for graph interactivity are handled in this file.
*/


GANETIVIZ_HELP_MODE = false;

// This function activates help mode.
function activate_help(){
    if (GANETIVIZ_HELP_MODE == false){
        GANETIVIZ_HELP_MODE = true
        console.log("Help Mode switched ON")
        // $("#cy").css({'width': '70%', })
        $("#overlay-help").css({'visibility':'visible',})
    } else {
        GANETIVIZ_HELP_MODE = false
        $("#overlay-help").css({'visibility':'hidden',})
        // $("#cy").css({ 'width': '100%'})
    }
}

/******************** [2] Cytoscape Viewport Rendering and Interactivity ***********************/
/**********************************************************************************************/

function renderinteractivegraph(){

  $('#cy').cytoscape({
    showOverlay: false,

    layout: {
      name: 'preset'
    },

    minZoom: 0.1,
    maxZoom: 10,

    // renderer: //TODO: This is something interesting, can be further useful for finer control.
    
    // Adding style to "cytoscape elements" ie. Nodes & Edges
    style: cytoscape.stylesheet()
      .selector('node.ganeti-node')
        .css({
          'shape': 'ellipse',
          'height': 'mapData(weight, 40, 80, 10, 30)',
          'width': 'mapData(weight, 40, 80, 10, 30)',
          'content': 'data(name)',
          'text-valign': 'center',
          'text-outline-width': 1,
          'text-outline-color': 'data(color)',
          'background-color': 'data(color)',
          //'text-outline-color': '#6FB1FC',
          //'background-color': '#6FB1FC',
          'color': '#fff'
        })
      .selector('node.ganeti-instance')
        .css({
          'shape': 'rectangle',
          'height':2,
          'width': 20,
          'content': 'data(name)',
          'text-valign': 'center',
          'text-outline-width': 0.6,
          'font-size':5,
          'text-outline-color': 'data(color)',
          'background-color': 'data(color)',
          'color': '#fff',
          //'text-outline-color': '#FC6FB1',
          //'background-color': '#FC6FB1',
          'visibility':'hidden',
        })
      .selector('node.ganeti-instance.highlighted')
        .css({
          'visibility':'visible',
          //'text-outline-color': 'green',
          'background-color': 'white',
        })
      .selector(':selected')
        .css({
          'border-width': 2,
          'border-color': '#333'
        })
      .selector('edge')
        .css({
          'width': 'mapData(strength, 0, 100, 0, 25)',
          'target-arrow-shape': 'triangle',
          'source-arrow-shape': 'none',
          'line-color': 'data(color)',
          'source-arrow-color': 'data(color)',
          'target-arrow-color': 'data(color)'
        })
      .selector('edge.instance-edge')
        .css({
          'target-arrow-shape': 'none'
        })
      .selector('edge.active')
        .css({
          'line-color':"red",
          'target-arrow-color':"red"
        })
      .selector('.faded')
        .css({
          'opacity': 0.25,
          'text-opacity': 0
        }),

    // Adding elements from abstract structures already created above.
    elements: {
      nodes: CytoNodeList,
      edges: CytoEdgeList,
    },
    
    ready: function(){
      window.cy = this;


      // Shows all the primary instances for a given node.
      cy.on('click', 'node.ganeti-node', function(event){
          $("#instancelist-div").css({'visibility':'visible'})

          class_string = '.pnode-' + fqdntoid(this.id())
          //console.log(class_string)

          // Collection of instances attached to the node clicked upon.
          window.primary_instances = cy.$(class_string)

          //// Primary Instances around this node are shown in a div.
          var li_elements = ""
          primary_instances.each(function(i, ele){
              pinstance = ele['_private']['data']['id']
              //console.log(pinstance)
              li_elements += "<li><div class='list-instance-element' id='" + pinstance + "'>" +  pinstance + "</div></li>"
          });

          $("#instancelist").html(li_elements)
         

          // After the list instance elements are created we bind them to the click event
          $(".list-instance-element").click(function(){
              $(".list-instance-element").toggleClass('active-list-element',false);
              $(this).addClass("active-list-element");

              //console.log(this.id)
              var instance_id = this.id
              pnode = VMGraph[instance_id][0];
              snode = VMGraph[instance_id][1];
              snode_edge_selector = "edge[source='" + pnode + "'][target='" + snode + "']";

              // First un-highlight all highlighted failover edges.
              cy.$('edge').toggleClass("active",false);

              //console.log(snode_edge_selector);
              eles = cy.$(snode_edge_selector)
              eles.toggleClass("active",true);
          });
 
      });


      // Highlights the edge indicating failover direction.
      cy.on('mousedown', 'node.ganeti-instance', function(event){
      //cy.$('node.ganeti-instance').click(function(){
          cy.$('edge').toggleClass("active",false);
          pnode = VMGraph[this.id()][0];
          snode = VMGraph[this.id()][1];
          snode_edge_selector = "edge[source='" + pnode + "'][target='" + snode + "']";
          //console.log(snode_edge_selector);
          eles = cy.$(snode_edge_selector)
          eles.toggleClass("active",true);
      });

    }
  });


  // InputBox Instance-Node Search Feature.
  function vertexSearch(e) {
      if (e.keyCode == 13) {
          text = $('instancelookup').val() // get the current value of the input field.
          var node_selector = "node[name ^='" + text + "']";
          //console.log(node_selector);
          cy_selected_instance = cy.$(node_selector)
          if (cy_selected_instance){
              // Un-highlight all the instances first.
              cy.$(".ganeti-instance").toggleClass("highlighted",false)
              //cy_selected_instance.toggleClass("active",true)
              cy_selected_instance.addClass("highlighted")
              cy_selected_instance.css({'visibility':'visible',})
          }
      }
  }

  // Double clicking on the instance lookup box clears it.
  $("#instancelookup-div").dblclick(function(e){
      $("#instancelookup-div").val("")
  });

  $("#instancelookup-div").keydown(function(e){
      // console.log(e.keyCode)
      if (e.keyCode == 13) {
          text = $('#instancelookup-div').val() // get the current value of the input field.
          var node_selector = "node[name ^='" + text + "']";
          //console.log(node_selector);
          cy_selected_instance = cy.$(node_selector)
          console.log(cy_selected_instance)
          if (cy_selected_instance){
              // Un-highlight all the instances first.
              cy.$(".ganeti-instance").toggleClass("highlighted",false)
              //cy_selected_instance.toggleClass("active",true)
              cy_selected_instance.addClass("highlighted")
              cy_selected_instance.css({'visibility':'visible',})
          }
      }

  });

}


// Other Keyboard Events
$(document).keydown(function(e){
    console.log(e.keyCode)

    // Panning the Graph using arrow keys
    if (e.keyCode == 37) { 
        // go right
        cy.panBy({
            x: 25,
            y: 0 
        });
       return false;
    }
    if (e.keyCode == 39) { 
        // go left
        cy.panBy({
            x: -25,
            y: 0 
        });
       return false;
    }
    if (e.keyCode == 38) { 
        // go down
        cy.panBy({
            x: 0,
            y: 25 
        });
       return false;
    }
    if (e.keyCode == 40) { 
        // go up
        cy.panBy({
            x: 0,
            y: -25 
        });
       return false;
    }


    // Character 'c' is pressed == All the visible instances are cleared. (Actually hidden)
    if (e.keyCode == 67) { 
        cy.$('.ganeti-instance').css({'visibility':'hidden'})
    }

    // Character 'p' is pressed == All the primary instances are shown attached to the node.
    if (e.keyCode == 80) {
        ele = cy.$(':selected')[0]
        if (ele != null && ele['_private']['classes']['ganeti-node'] == true){
            pnode = ele['_private']['data']['id']

          class_string = '.pnode-' + fqdntoid(pnode)
          //console.log(class_string)

          // Collection of instances attached to the node clicked upon.
          primary_instances = cy.$(class_string)

          //// Primary Instances around this node are shown.
          //primary_instances.css({visibility:'visible'})
          // If the set of primary instances around this node is already visible then hide them, else show them.
          if (primary_instances.css('visibility') == 'visible'){
              primary_instances.css({visibility:'hidden'})
          }else {
              primary_instances.css({visibility:'visible'})
          }
      }
    }

    // Character 's' is pressed == All the secondary instances corresponding to the highlighted node pop up.
    if (e.keyCode == 83) { 
        ele = cy.$(':selected')[0]
        if (ele != null && ele['_private']['classes']['ganeti-node'] == true){
            cy.$('.ganeti-instance').css({'visibility':'hidden'})
            snode = ele['_private']['data']['id']
            sec_instances_selector = '.snode-' + fqdntoid(snode)
            sec_instances = cy.$(sec_instances_selector)
            //console.log(sec_instances_selector)
            sec_instances.css({'visibility':'visible'})
            //sec_instances.toggleClass('highlighted-sinstances',true)
        }
    }


    // If Character 'h' is pressed then switch help mode on.
    if (e.keyCode == 72) { 
        activate_help()
    }

    // If Character 'r' is pressed then we reset the graph to the original position (without refreshing the cluster)
    if (e.keyCode == 82) { 
        buildabstractgraph()
        renderinteractivegraph()
    }
});

$("#help-div").click(function(){
    activate_help()
});

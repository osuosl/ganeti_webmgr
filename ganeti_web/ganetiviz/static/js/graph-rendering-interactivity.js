/*
(c) OSU | Open Source Lab, Pranjal Mittal

This file includes code for rendering of Ganetiviz Graph and Interactivity.
All events for graph interactivity are handled in this file.
*/


HELP_MODE = false;

/******************** [2] Cytoscape Viewport Rendering and Interactivity ***********************/
/**********************************************************************************************/
$('#cy').cytoscape({
  showOverlay: false,

  layout: {
    name: 'preset'
  },
  
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

/*
    // To make Primary Instances corresponding to a Ganeti-Node visible.
    cy.$('node.ganeti-node').click(function(){
        // First hide any of the instance-vertices that are already visible.
        //cy.$(".ganeti-instance").css({visibility:"hidden"});

        console.log(this.id())

        // Now, show the instance vertices corresponding to this node (being clicked)
        var branches_selector = "edge[source='" + this.id() + "']";
        // Make target of each branch ending at an instance vertice visible.
        cy.$(branches_selector).filter(".instance-edge").each(function(i, branch){
            instance_element = branch.target()[0]
            //console.log(instance_element['_private']['data']['name'])
            if (instance_element.css('visibility') == 'visible'){
                instance_element.css({visibility:'hidden'})
            }else if (instance_element.css('visibility') == 'hidden'){
                instance_element.css({visibility:'visible'})
            }
        });
    });
*/

    cy.$('node.ganeti-node').mousedown(function(){
        class_string = '.pnode-' + fqdntoid(this.id())
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
    });

    // Highlights the edge indicating failover direction.
    cy.$('node.ganeti-instance').click(function(){
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
        text = $('#vertexInput').val() // get the current value of the input field.
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


// Panning by pressing arrow keys
$(document).keydown(function(e){
    //console.log(e.keyCode)

    if (e.keyCode == 37) { 
        // go left
        cy.panBy({
            x: -25,
            y: 0 
        });
       return false;
    }
    if (e.keyCode == 39) { 
        // go right
        cy.panBy({
            x: 25,
            y: 0 
        });
       return false;
    }
    if (e.keyCode == 38) { 
        // go up
        cy.panBy({
            x: 0,
            y: -25 
        });
       return false;
    }
    if (e.keyCode == 40) { 
        // go down
        cy.panBy({
            x: 0,
            y: 25 
        });
       return false;
    }

    // Character 'c' is pressed == All the visible instances are cleared. (Actually hidden)
    if (e.keyCode == 67) { 
        cy.$('.ganeti-instance').css({'visibility':'hidden'})
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
       return false;
    }


    if (e.keyCode == 72) { 
        if (HELP_MODE == false){
            HELP_MODE = true
            console.log("Help Mode switched ON")
            // $("#cy").css({'width': '70%', })
            $("#overlay-help").css({'visibility':'visible',})
        } else {
            HELP_MODE = false
            $("#overlay-help").css({'visibility':'hidden',})
            // $("#cy").css({ 'width': '100%'})
        }
    }
});



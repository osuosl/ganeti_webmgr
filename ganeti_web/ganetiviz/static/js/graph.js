/*
(c) Pranjal Mittal, OSU Open Source Lab
*/


/******* [1] Abstract Graph Manipulation, Creating Appropriate Object Represnetations **********/
/**********************************************************************************************/

syscenter = {x:500,y:500} // Center of the whole System
var pp = polypointscircle(syscenter,200,5)

CytoNodeList = []            // A list of node objects in a format required by Cytoscape JS will be added to this list.
CytoEdgeList = []           // A list of edge objects in a format required by Cytoscape JS will be added to this list.
CytoNodePositions = {}     // Stores the rendering position of the Gnodes for each node.

VMGraph = {}               // A HashMap object that will contain mapping from VM to pnode or snode for fast search, and parent object lookup.
FailoverLinks = {}        // FailoverLinks will contain number of failover possibilities b/n a PNode & an SNode.
NodeInstanceLinks = {}   // HashMap from Node to NUMBER of primary Instances.

/*
[1.1][gnodes_json_1]
- Adds all GanetiNodes to "CytoNodeList" in format required for rendering with Cytoscape.
  (The GanetiInstances are not added to the list in a later block)
*/
var loop_index = 0;
gnodes_json.forEach(function(node) {
    gnode = node["fields"]["hostname"]
    position = pp[loop_index]
    CytoNodePositions[gnode] = position

    // Adding the ganeti nodes to the Cytoscape NodeList
    cytoscape_node_obj =       
      {data: { id: gnode, name: gnode, weight: 100,},
        position: position, classes:'ganeti-node'};
    CytoNodeList.push(cytoscape_node_obj);

    loop_index += 1
});



/*
[1.2][vms_json_1]: First loop over each Virtual Machine object
- Adds items to "VMGraph"
- Adds items to "FailoverLinks"
- Adds items to "NodeInstanceLinks"
*/
vms_json.forEach(function(vm) {
    vm_hostname = vm["fields"]["hostname"]
    pnode = vm["fields"]["primary_node"]    // A Ganeti Node referred ahead as (g)node
    snode = vm["fields"]["secondary_node"]  // (g)node

    // A HashMap object that will contain mapping from VM to pnode or snode for fast search
    VMGraph[vm_hostname] = [pnode,snode]

    // Counting number of instances of each (g)node.
    if (!NodeInstanceLinks[pnode]){
        NodeInstanceLinks[pnode] = 1
    }
    else{
        NodeInstanceLinks[pnode] += 1
    }

    // FailoverLinks will contain number of failover possibilities b/n a PNode & an SNode.
    if (snode != null){
        if (!FailoverLinks[pnode]){
            FailoverLinks[pnode] = {}
        }

        if (!FailoverLinks[pnode][snode]){
            FailoverLinks[pnode][snode] = 1
        }
        else{
            FailoverLinks[pnode][snode] += 1
      }
    }
});



//[1.3] Computing graph rendering positions for VirtualMachine vertices.
//    VM's should lie on a circle around their respective primary node at regular intervals for clean display.
VMPositions = {}  // A HashMap object defining VM positions for each (g)node.
for (nodekey in NodeInstanceLinks){
    N = NodeInstanceLinks[nodekey] 
    node_position = CytoNodePositions[nodekey]    // We are going to generate points around this coordinate lying on a circle.
    R = 30                                       // Setting R constant for now. #TODO Check optimal value.
    VMPositions[nodekey] = polypointscircle(center=node_position,R,N)
}


/*
[1.4][vms_json_2]:: Second loop over each VM object makes use of objects built in first loop.
- This is necessary and contents cannot be shifted to 1st loop.
- Adds all GanetiInstance objects to "CytoNodeList", making it an exhaustive list of vertice objects.
- Adds only the GanetiNode-Instance-Edges to "CytoEdgeList", 
  (Node-Node edges still need to be added)
*/
vms_json.forEach(function(vm) {

    vm_hostname = vm["fields"]["hostname"]
    pnode = vm["fields"]["primary_node"]    // (g)node

    // Adding Cytoscape Graph Vertices representing Instances
    cytoscape_node_obj =  {
         data: { id: vm_hostname, name: vm_hostname, weight: 0.05,},
	       position: VMPositions[pnode].pop(),
         classes:'ganeti-instance' }
    CytoNodeList.push(cytoscape_node_obj);

    // Adding Cytoscape Graph Edges: (g)Node-Instance edges.
    cytoscape_edge_obj = { data: { source: pnode, target: vm_hostname, color: '#6FFCB1', strength:1 }, classes: 'instance-edge'};
    CytoEdgeList.push(cytoscape_edge_obj);

});
//Note: Having 2 similar loop introduces a very small (constant factor) performance overhead, but is logically essential here.



// [1.5] Adding the remaining Cytoscape Graph Edges: (g)Node-(g)Node edges
for (sourcenodekey in FailoverLinks) {
    for (targetnodekey in FailoverLinks[sourcenodekey]){
        cytoscape_edge_obj = { data: { source: sourcenodekey, target: targetnodekey, 
                               color: '#6FB1FC', strength: FailoverLinks[sourcenodekey][targetnodekey] }};
        CytoEdgeList.push(cytoscape_edge_obj);
    }
};


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
        'text-outline-color': '#6FB1FC',
        'background-color': '#6FB1FC',
        'color': '#fff'
      })
    .selector('node.ganeti-instance')
      .css({
        'shape': 'rectangle',
        'height':2,
        'width': 20,
        'content': 'data(name)',
        'text-valign': 'center',
        'text-outline-width': 0.5,
        'font-size':3,
        'text-outline-color': '#FC6FB1',
        'background-color': '#FC6FB1',
        'color': '#fff',
        'visibility':'hidden',
      })
    .selector('node.ganeti-instance.highlighted')
      .css({
        'visibility':'visible',
        'text-outline-color': 'brown',
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

    // To make Primary Instances corresponding to a Ganeti-Node visible.
    cy.$('node.ganeti-node').click(function(){
        // First hide any of the instance-vertices that are already visible.
        cy.$(".ganeti-instance").css({visibility:"hidden"});
        // Now, show the instance vertices corresponding to this node (being clicked)
        var branches_selector = "edge[source='" + this.id() + "']";
        // Make target of each branch ending at an instance vertice visible.
        cy.$(branches_selector).filter(".instance-edge").each(function(i, branch){
            branch.target()[0].css({visibility:'visible'});
        });
    });

    // Highlights the edge indicating failover direction.
    cy.$('node.ganeti-instance').mousedown(function(){
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
        console.log(node_selector);
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

// Panning by pressing arrow keys (Work in progress)
/*
$("#cy").keypress(function (event) {
  // handle cursor keys
  if (event.keyCode == 37) {
    // go left
  } else if (event.keyCode == 39) {
    // go right
  }
});
*/

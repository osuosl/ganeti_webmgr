/*
(c) OSU | Open Source Lab, Pranjal Mittal
*/


/******* [1] Abstract Graph Manipulation, Creating Appropriate Object Represnetations **********/
/**********************************************************************************************/

function buildabstractgraph(){

  syscenter = {x:500,y:500} // Center of the whole System
  var pp = polypointscircle(syscenter,200,5)

  window.CytoNodeList = []            // A list of node objects in a format required by Cytoscape JS will be added to this list.
  window.CytoEdgeList = []           // A list of edge objects in a format required by Cytoscape JS will be added to this list.
  var CytoNodePositions = {}     // Stores the rendering position of the Gnodes for each node.

  window.VMGraph = {}               // A HashMap object that will contain mapping from VM to pnode or snode for fast search, and parent object lookup.
  var FailoverLinks = {}        // FailoverLinks will contain number of failover possibilities b/n a PNode & an SNode.
  var NodeInstanceLinks = {}   // HashMap from Node to NUMBER of primary Instances.

  /*
  [1.1][gnodes_json_1]
  - Adds all GanetiNodes to "CytoNodeList" in format required for rendering with Cytoscape.
    (The GanetiInstances are not added to the list in a later block)
  */
  var loop_index = 0;
  gnodes_json.forEach(function(node) {
      gnode = node["fields"]["hostname"]
      offline = node["fields"]["offline"]
      position = pp[loop_index]
      CytoNodePositions[gnode] = position

      gnode_color = '#6FB1FC'
      if (offline){
          //console.log("Offline!")
          gnode_color = '#DD2222'
      }


      // Adding the (g)nodes ie. Ganeti Nodes to the Cytoscape NodeList
      cytoscape_node_obj =       
        {data: { id: gnode, name: gnode, weight: 100,color:gnode_color},
          position: position, classes:'ganeti-node', locked: true};
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
      owner = vm["fields"]["owner"]
      os = vm["fields"]["operating_system"]
      ram = vm["fields"]["ram"]
      minram = vm["fields"]["minram"]
      status = vm["fields"]["status"]


      // A HashMap object that will contain mapping from VM to pnode or snode for fast search
      VMGraph[vm_hostname] = [pnode,snode,owner,os,ram,minram,status]

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
      R = 50                                       // Setting R constant for now. #TODO Check optimal value.
      VMPositions[nodekey] = polypointscircle(center=node_position,R,N)
  }


  /*
  [1.4][vms_json_2]:: Second loop over sorted VM object makes use of objects built in first loop.
  - This is necessary and contents cannot be shifted to 1st loop.
  - Adds all GanetiInstance objects to "CytoNodeList", making it an exhaustive list of vertice objects.
  - Adds only the GanetiNode-Instance-Edges to "CytoEdgeList", 
    (Node-Node edges still need to be added)
  - Beautiful Idea: Sorting out instances around every node, boils down to sorting all instances first
    and then adding them around whichever node it belongs to sequentially. :)
  */
  vms_json_sorted = vms_json.sort(function(a,b) {return a.fields.hostname - b.fields.hostname });
  vms_json_sorted.forEach(function(vm) {

      vm_hostname = vm["fields"]["hostname"]
      pnode = vm["fields"]["primary_node"]    // (g)node
      snode = vm["fields"]["secondary_node"]
      vm_status = vm["fields"]["status"]

      // Assigning a color to instances as per status. green for "running" instance, red for the rest.
      vm_color = '#AA0000'
      if (vm_status == "running"){
          vm_color = '#00CC00'
      }

      // Adding classes to each instance vertice that make its selection convenient.
      instance_classes_string = 'ganeti-instance ' + 'pnode-' + fqdntoid(pnode) + ' snode-' + fqdntoid(snode)

      // Adding Cytoscape Graph Vertices representing Instances
      cytoscape_node_obj =  {
           data: { id: vm_hostname, name: vm_hostname, weight: 0.05,color: vm_color},
	         position: VMPositions[pnode].pop(),
           classes:instance_classes_string }
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
                                 color: '#6FB1FC', strength: FailoverLinks[sourcenodekey][targetnodekey] }, classes: 'node-edge'};
          CytoEdgeList.push(cytoscape_edge_obj);
      }
  };

};

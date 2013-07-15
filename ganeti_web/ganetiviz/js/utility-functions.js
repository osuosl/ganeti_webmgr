/*
Copyright (c): Pranjal Mittal, OSUOSL

(1) A collection of custom useful functions for use in graph.js.
*/

function rbt(a,b){
    // Returns random real number between a & b
    return (Math.random() * b) + a
}

function polypointscircle(center,R,N) {
    // Returns an array with the coodrdinates of a regular polygon (which lie on a circle with a center)
    var polypoints = new Array();
    for (i=0; i<N; i++){
      alpha = i * (2*Math.PI)/N + (Math.PI/2);
      x = center.x + R*Math.cos(alpha)
      y = center.y - R*Math.sin(alpha)
      polypoints.push({x:x,y:y})
    }
    return polypoints;
};

function rndisc(pt,r,R){
    // Generates a coordinate such that it lies inside a disc centered at Point "pt" from r to R. (randomly)
    // pt = {x:<some_value>,y:<some_value>}
    alpha = rbt(0,2*Math.PI)
    var coordinates = new Array();
    l = rbt(r,R)
    x = pt.x + l*Math.cos(alpha)
    y = pt.y - l*Math.sin(alpha)
    return {x:x,y:y}
}

function modrndisc(pt,r,R,syscenter){
    /* Modified form of rndisc() function (under construction)
       Returns a coordinate such that it lies in a disc near the pnode with the additional constraint-
       It shall lie on the other side of the tangent to the pnodes-circle whose center is at syscenter..
       The tangent would be perpendicular to the line joinign syscenter & pt.
       This is useful when it is required to avoid clutter in the visualization. */
    // pt = {x:<some_value>,y:<some_value>}
    // syscenter = Center of the whole system, format is same as pt.
    var sc = syscenter;
    var adjustment = 0 //(Math.PI / 12)
    theta = (Math.PI / 2) - Math.atan2(sc.y-pt.y,pt.x-sc.x);
    alpha = rbt(-theta + adjustment, (Math.PI - theta) - adjustment)
    var coordinates = new Array();
    l = rbt(r,R)
    x = pt.x + l*Math.cos(alpha)
    y = pt.y - l*Math.sin(alpha)
    return {x:x,y:y}
}


function fqdntoid(fqdn){
    // To replace "." by "-" in a Fully Qualified Domain Name.
    return fqdn.replace(/\./g,"-")
}


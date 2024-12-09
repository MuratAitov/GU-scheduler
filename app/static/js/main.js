function visualizeGraph(treeData) {
    const levels = treeData.levels;
    const edges = treeData.edges;

    let edge_x = [];
    let edge_y = [];
    let node_x = [];
    let node_y = [];
    let node_text = [];
    let node_shapes = [];
    let node_colors = [];

    // Calculate node positions
    levels.forEach((lvl, lvlIndex) => {
        let count = lvl.nodes.length;
        let spacing = 1 / (count + 1);
        lvl.nodes.forEach((nodeObj, i) => {
            let x = (i + 1) * spacing;  // Evenly distribute nodes on x-axis
            let y = -lvlIndex;          // Deeper levels lower on y-axis
            node_x.push(x);
            node_y.push(y);

            // Format node text
            let label = formatNodeLabel(nodeObj.label || nodeObj.id);
            node_text.push(label);
            
            node_shapes.push(getNodeShape(nodeObj.data.type));
            node_colors.push(getNodeColor(nodeObj.data.type));
            nodeObj._x = x;
            nodeObj._y = y;
        });
    });

    // Process edges
    edges.forEach(edgeLevel => {
        edgeLevel.edges.forEach(e => {
            let fromNode = findNode(levels, e.from);
            let toNode = findNode(levels, e.to);
            if (fromNode && toNode) {
                edge_x.push(fromNode._x, toNode._x, null);
                edge_y.push(fromNode._y, toNode._y, null);
            }
        });
    });

    // Add edge hover text
    let edge_hover_text = edges
        .map(edgeLevel =>
            edgeLevel.edges.map(e => {
                let fromNode = findNode(levels, e.from);
                let toNode = findNode(levels, e.to);
                return `${fromNode.label} → ${toNode.label}`;
            })
        )
        .flat();

    // Define edge trace for Plotly
    let edge_trace = {
        x: edge_x,
        y: edge_y,
        mode: 'lines',
        line: { width: 2, color: '#888' },
        hoverinfo: 'text',
        text: edge_hover_text,
        type: 'scatter'
    };

    // Define node trace for Plotly
    let node_trace = {
        x: node_x,
        y: node_y,
        mode: 'markers+text',
        text: node_text,
        textposition: "top center",
        hoverinfo: 'text',
        marker: {
            size: 15,
            symbol: node_shapes,  // Use custom shapes
            color: node_colors,    // Custom colors based on type
            line: { width: 2, color: '#333' }
        },
        type: 'scatter'
    };

    // Define layout for the graph
    var layout = {
        title: 'Prerequisite Dependency Graph',
        showlegend: false,
        hovermode: 'closest',
        xaxis: { showgrid: false, zeroline: false, showticklabels: false },
        yaxis: { showgrid: false, zeroline: false, showticklabels: false },
        margin: { l: 50, r: 50, b: 50, t: 100 },
        dragmode: 'zoom'  // Enable zoom functionality
    };

    // Render the graph using Plotly
    Plotly.newPlot('graph', [edge_trace, node_trace], layout, { scrollZoom: true });
}

// Function to determine the correct shape for each node
function getNodeShape(type) {
    switch (type.toUpperCase()) {
        case "OR":
            return "triangle-up";     // OR Condition → Circle
        case "AND":
            return "square";     // AND Condition → Square
        case "COURSE":
        default:
            return "circle";  // Course → Triangle
    }
}

// Function to determine node color
function getNodeColor(type) {
    switch (type.toUpperCase()) {
        case "OR":
        case "AND":
            return "black";      // OR/AND conditions → Black
        case "COURSE":
        default:
            return "lightblue";  // Courses → Light blue
    }
}

// Helper function to format labels
function formatNodeLabel(label) {
    if (label.toUpperCase() === "OR" || label.toUpperCase() === "AND") {
        return label.toUpperCase();  // Ensure OR/AND are uppercase
    }
    return label;  // Keep other labels unchanged
}

// Helper function to find nodes by ID
function findNode(levels, id) {
    for (let lvl of levels) {
        for (let n of lvl.nodes) {
            if (n.id === id) return n;
        }
    }
    return null;
}

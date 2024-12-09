function visualizeGraph(treeData) {
    // Предположим, treeData содержит levels и edges
    // Примерно так же, как в вашем JSON

    // Мы можем использовать Plotly для рендеринга, как в примере visualize_tree_plotly, но теперь на фронте.
    // Однако у нас нет pos-координат готовых. Можно или статически расположить узлы, или использовать force-layout на фронте.

    // Для упрощения примера предположим, что мы хотим просто вывести уровни по вертикали,
    // и расположить узлы каждого уровня по оси x равномерно.

    const levels = treeData.levels;
    const edges = treeData.edges;

    let edge_x = [];
    let edge_y = [];
    let node_x = [];
    let node_y = [];
    let node_text = [];

    // Рассчитываем позиции узлов (x, y)
    // Уровень -> y-координата, узлы в уровне равномерно распределены по x

    levels.forEach((lvl, lvlIndex) => {
        let count = lvl.nodes.length;
        let spacing = 1/(count+1);
        lvl.nodes.forEach((nodeObj, i) => {
            let x = (i+1)*spacing;
            let y = -lvlIndex; // чем дальше уровень, тем ниже по y
            node_x.push(x);
            node_y.push(y);
            node_text.push(nodeObj.label || nodeObj.id);
            nodeObj._x = x;
            nodeObj._y = y;
        });
    });

    // Теперь edges
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

    let edge_trace = {
        x: edge_x, y: edge_y,
        mode: 'lines',
        line: {width: 2, color: '#888'},
        type: 'scatter'
    };

    let node_trace = {
        x: node_x,
        y: node_y,
        mode: 'markers+text',
        text: node_text,
        textposition: "top center",
        hoverinfo: 'text',
        marker: {
            size: 10,
            color: 'lightblue',
            line: {width: 2, color: '#333'}
        },
        type: 'scatter'
    };

    var layout = {
        title: 'Dependency Graph',
        showlegend: false,
        hovermode: 'closest',
        xaxis: {showgrid: false, zeroline: false},
        yaxis: {showgrid: false, zeroline: false},
        // dragmode: 'pan' включён по умолчанию в plotly для графиков, можно включить zoom
    };

    Plotly.newPlot('graph', [edge_trace, node_trace], layout, {scrollZoom: true});
}

function findNode(levels, id) {
    for (let lvl of levels) {
        for (let n of lvl.nodes) {
            if (n.id === id) return n;
        }
    }
    return null;
}

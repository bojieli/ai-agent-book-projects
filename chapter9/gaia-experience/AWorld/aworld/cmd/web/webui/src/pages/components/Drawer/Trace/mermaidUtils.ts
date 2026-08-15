interface TraceNode {
  show_name: string;
  span_id?: string;
  duration_ms?: number;
  children?: TraceNode[];
}

export function treeToMermaid(input: any): string {
  let output = 'flowchart TD\n';
  const processedNodes = new Set<string>();

  function processNode(node: TraceNode, parentId?: string) {
    if (!node?.show_name) return;
    
    const rawNodeId = `${node.show_name}_${node.span_id || ''}`.replace(/\s+/g, '_');
    const cleanNodeId = rawNodeId.replace(/[^a-zA-Z0-9_]/g, '_');
    
    if (!processedNodes.has(cleanNodeId)) {
      const cleanName = node.show_name
        .replace(/[^a-zA-Z0-9-\s\-_.,]/g, '')
        .trim();
      
      output += `  ${cleanNodeId}["${cleanName}"]\n`;
      processedNodes.add(cleanNodeId);
    }

      if (parentId) {
        const cleanParentId = parentId.replace(/[^a-zA-Z0-9_]/g, '_');
        const duration = node.duration_ms ? `${node.duration_ms.toFixed(2)}ms` : '';
        output += `  ${cleanParentId} -->|${duration}| ${cleanNodeId}\n`;
    }

    if (node.children && node.children.length > 0) {
      node.children.forEach((child: TraceNode) => processNode(child, cleanNodeId));
    }
  }

  if (!input) return output;

  const rootNode: TraceNode = {
    show_name: 'Trace Root',
    span_id: 'root',
    children: [] as TraceNode[]
  };

  if (input.data && Array.isArray(input.data)) {
    rootNode.children = input.data;
  } else if (Array.isArray(input)) {
    rootNode.children = input;
  } else {
    rootNode.children = [input];
  }

  processNode(rootNode);

  return output;
}

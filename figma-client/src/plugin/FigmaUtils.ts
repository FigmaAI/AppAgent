import { ParsedReport, ParsedRound } from '../typings/types';

export function createText(characters: string, fontSize: number, fontStyle: 'Regular' | 'Bold'): TextNode {
  const text = figma.createText();
  text.characters = characters;
  text.fontSize = fontSize;
  text.fontName = { family: 'Inter', style: fontStyle };
  text.textAutoResize = 'WIDTH_AND_HEIGHT';
  return text;
}

export function createTextFrame(title: string, content: string, r?: number, g?: number, b?: number): FrameNode {
  const frame = figma.createFrame();
  frame.name = title;

  const titleText = createText(title, 32, 'Bold');
  if (r !== undefined && g !== undefined && b !== undefined) {
    titleText.fills = [{ type: 'SOLID', color: { r, g, b } }];
  }

  const decodedContent = content.replace(/\\(.)/g, '$1');
  const contentText = createText(decodedContent, 24, 'Regular');
  if (r !== undefined && g !== undefined && b !== undefined) {
    contentText.fills = [{ type: 'SOLID', color: { r, g, b } }];
  }

  frame.appendChild(titleText);
  frame.appendChild(contentText);

  frame.layoutMode = 'VERTICAL';
  frame.itemSpacing = 16;
  frame.counterAxisSizingMode = 'FIXED';
  frame.resize(1000, frame.height);
  frame.primaryAxisSizingMode = 'AUTO';
  frame.fills = [];

  titleText.layoutSizingHorizontal = 'FILL';
  contentText.layoutSizingHorizontal = 'FILL';

  return frame;
}

// create a frame with a title and a content
export async function getOrCreateUTReportsFrame() {
  let frame = figma.currentPage.findOne((n) => n.type === 'FRAME' && n.name === 'UT Reports') as FrameNode;
  if (!frame) {
    frame = createUTReportsFrame();
    figma.currentPage.appendChild(frame);
  }
  return frame;
}

export function createUTReportsFrame() {
  const frame = figma.createFrame();
  frame.name = 'UT Reports';
  frame.layoutMode = 'HORIZONTAL';
  frame.itemSpacing = 128;
  frame.primaryAxisSizingMode = 'AUTO';
  frame.counterAxisSizingMode = 'AUTO';
  frame.cornerRadius = 16;
  const maxX = figma.currentPage.children.reduce((max, node) => Math.max(max, node.x + node.width), 0);
  frame.x = maxX + 100;
  frame.y = 0;
  return frame;
}

export function createTaskFrame(taskName: string) {
  const frame = figma.createFrame();
  frame.name = taskName;
  frame.layoutMode = 'VERTICAL';
  frame.itemSpacing = 64;
  frame.primaryAxisSizingMode = 'AUTO';
  frame.counterAxisSizingMode = 'AUTO';
  return frame;
}

export function createNameFrame(nodeName: string) {
  const frame = figma.createFrame();
  frame.name = 'Name';
  frame.layoutMode = 'HORIZONTAL';
  frame.paddingTop = frame.paddingBottom = frame.paddingLeft = frame.paddingRight = 64;
  frame.cornerRadius = 16;
  frame.primaryAxisSizingMode = 'AUTO';
  frame.counterAxisSizingMode = 'AUTO';

  const text = figma.createText();
  text.characters = nodeName;
  text.fontSize = 64;
  text.fontName = { family: 'Inter', style: 'Bold' };
  text.textAutoResize = 'WIDTH_AND_HEIGHT';
  frame.appendChild(text);

  return frame;
}

export function createTaskDescFrame(taskDesc: string, personaDesc?: string) {
  const frame = figma.createFrame();
  frame.name = 'task_desc';
  frame.layoutMode = 'VERTICAL';
  frame.paddingTop = frame.paddingBottom = frame.paddingLeft = frame.paddingRight = 64;
  frame.itemSpacing = 48;
  frame.cornerRadius = 16;
  frame.primaryAxisSizingMode = 'AUTO';
  frame.counterAxisSizingMode = 'AUTO';

  const titleText = createText('Task Description', 48, 'Bold');
  frame.appendChild(titleText);

  const descText = createText(taskDesc, 24, 'Regular');
  frame.appendChild(descText);

  if (personaDesc) {
    const personaText = createText(personaDesc, 24, 'Regular');
    frame.appendChild(personaText);
  }

  return frame;
}

export function createAnatomyFrame(roundCount: number): FrameNode {
  const frame = figma.createFrame();
  frame.name = 'anatomy';
  frame.layoutMode = 'VERTICAL';
  frame.paddingTop = frame.paddingBottom = frame.paddingLeft = frame.paddingRight = 64;
  frame.itemSpacing = 32;
  frame.primaryAxisSizingMode = 'AUTO';
  frame.counterAxisSizingMode = 'AUTO';

  const titleText = createText(`Round ${roundCount}`, 48, 'Bold');
  frame.appendChild(titleText);

  return frame;
}

export function createPreviewFrame(): FrameNode {
  const frame = figma.createFrame();
  frame.name = 'preview';
  frame.layoutMode = 'HORIZONTAL';
  frame.paddingTop = frame.paddingBottom = frame.paddingLeft = frame.paddingRight = 64;
  frame.itemSpacing = 64;
  frame.fills = [{ type: 'SOLID', color: { r: 0, g: 0, b: 0 } }]; // set the black background
  frame.primaryAxisSizingMode = 'AUTO';
  frame.counterAxisSizingMode = 'AUTO';
  frame.cornerRadius = 16;

  return frame;
}

export async function addNodeImageToPreviewFrame(
  node: SceneNode
): Promise<{ imageHash: string; imageBytes: Uint8Array }> {
  const imageBytes = await node.exportAsync({ format: 'PNG' });
  const imageHash = figma.createImage(imageBytes).hash;
  return { imageHash, imageBytes };
}

export function createImageFrameFromHash(
  imageHash: string,
  width: number,
  height: number,
): FrameNode {
  const imageFrame = figma.createFrame();
  const imageNode = figma.createRectangle();
  imageNode.fills = [{ type: 'IMAGE', scaleMode: 'FILL', imageHash }];
  imageNode.resize(width, height);

  imageFrame.appendChild(imageNode);
  imageFrame.resize(width, height);

  return imageFrame;
}

export function parseReportContent(content: string): ParsedReport {
  const titleMatch = content.match(/# (.+)$/m);
  const taskNameMatch = content.match(/^(self_explore.+)$/m);
  const taskDescMatch = content.match(/## Task Description\s+([\s\S]*?)(?=##|$)/);
  const personaDescMatch = content.match(/## Persona Description\s+([\s\S]*?)(?=##|$)/);
  const rounds = content.split(/^## Round \d+$/m).slice(1);


  return {
    title: titleMatch? titleMatch[1].trim() : '',
    taskName: taskNameMatch? taskNameMatch[1].trim() : '',
    taskDesc: taskDescMatch ? taskDescMatch[1].trim() : '',
    personaDesc: personaDescMatch ? personaDescMatch[1].trim() : '',
    rounds: rounds.map(round => parseRound(round))
  };
}

export async function parseRound(roundContent: string): Promise<ParsedRound> {
  const imageRegex = /!\[.*?\]\((.*?)\)/g;
  const observationMatch = roundContent.match(/### Observation:\s+([\s\S]*?)(?=###|$)/);
  const thoughtMatches = roundContent.match(/### Thought:\s+([\s\S]*?)(?=###|$)/g);
  const actionMatch = roundContent.match(/### Action:\s+([\s\S]*?)(?=###|$)/);
  const summaryMatch = roundContent.match(/### Summary:\s+([\s\S]*?)(?=###|$)/);
  const decisionMatch = roundContent.match(/### Decision:\s+([\s\S]*?)(?=###|$)/);

  const imagePaths = [...roundContent.matchAll(imageRegex)].map(match => match[1]);
  const images = await Promise.all(imagePaths.map(async imagePath => {
    const response = await fetch('http://localhost:5000/get_image', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ file_path: imagePath })
    });
    const data = await response.json();
    return data.status === 'success' ? data.image_data : null;
  }));

  return {
    images: images.filter(img => img !== null),
    observation: observationMatch ? observationMatch[1].trim() : '',
    thoughts: thoughtMatches ? thoughtMatches.map(thought => thought.replace(/### Thought:\s+/, '').trim()) : [],
    action: actionMatch ? actionMatch[1].trim() : '',
    summary: summaryMatch ? summaryMatch[1].trim() : '',
    decision: decisionMatch ? decisionMatch[1].trim() : ''
  };
}


export async function createRoundElement(round: Awaited<ReturnType<typeof parseRound>>, roundCount: number) {
  const anatomyFrame = createAnatomyFrame(roundCount);
  const previewFrame = createPreviewFrame();
  anatomyFrame.appendChild(previewFrame);

  for (const base64Image of round.images) {
    const imageFrame = await createImageFrameFromBase64(base64Image);
    previewFrame.appendChild(imageFrame);
  }

  addTextFramesToPreview(previewFrame, round);

  return anatomyFrame;
}

async function createImageFrameFromBase64(base64Image: string) {
  const imageBuffer = figma.base64Decode(base64Image);
  const image = figma.createImage(imageBuffer);
  const { width, height } = await image.getSizeAsync();
  return createImageFrameFromHash(image.hash, width, height);
}

function addTextFramesToPreview(previewFrame: FrameNode, round: Awaited<ReturnType<typeof parseRound>>) {
  const responseFrame = figma.createFrame();
  // set background color to transparent
  responseFrame.fills = [];
  responseFrame.name = 'Klever UT Response';
  responseFrame.layoutMode = 'VERTICAL';
  responseFrame.itemSpacing = 16;
  responseFrame.primaryAxisSizingMode = 'AUTO';
  responseFrame.counterAxisSizingMode = 'AUTO';
  
  responseFrame.appendChild(createTextFrame('Observation', round.observation, 1, 1, 1));
  if (round.thoughts.length > 0) {
    responseFrame.appendChild(createTextFrame('Thought', round.thoughts[0], 1, 1, 1));
  }
  responseFrame.appendChild(createTextFrame('Action', round.action, 1, 1, 1));
  responseFrame.appendChild(createTextFrame('Summary', round.summary, 1, 1, 1));
  responseFrame.appendChild(createTextFrame('Decision', round.decision, 1, 1, 1));
  if (round.thoughts.length > 1) {
    responseFrame.appendChild(createTextFrame('Thought', round.thoughts[1], 1, 1, 1));
  }

  previewFrame.appendChild(responseFrame);
}



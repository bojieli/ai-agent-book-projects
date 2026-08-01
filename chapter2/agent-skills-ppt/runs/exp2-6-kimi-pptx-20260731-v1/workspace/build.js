const pptxgen = require('pptxgenjs');
const html2pptx = require('./kimi-skills/pptx/scripts/html2pptx.js');

async function build() {
  const pptx = new pptxgen();
  pptx.layout = 'LAYOUT_16x9';
  pptx.author = 'Kimi';
  pptx.title = 'Attention Is All You Need';

  // Slides 1-6
  await html2pptx('slides/01-cover.html', pptx);
  await html2pptx('slides/02-problem.html', pptx);
  await html2pptx('slides/03-keyidea.html', pptx);
  await html2pptx('slides/04-architecture.html', pptx);
  await html2pptx('slides/05-attention.html', pptx);
  await html2pptx('slides/06-building-blocks.html', pptx);

  // Slide 7: complexity table (adapted from Table 1, p. 6)
  const { slide: s7, placeholders: p7 } = await html2pptx('slides/07-why-self-attention.html', pptx);
  const hdr = { fill: { color: '4338CA' }, color: 'FFFFFF', bold: true, fontSize: 10 };
  const rows = [
    [
      { text: 'Layer Type', options: hdr }, { text: 'Complexity per Layer', options: hdr },
      { text: 'Sequential Ops', options: hdr }, { text: 'Max Path Length', options: hdr }
    ],
    ['Self-Attention', 'O(n²·d)', 'O(1)', 'O(1)'],
    ['Recurrent', 'O(n·d²)', 'O(n)', 'O(n)'],
    ['Convolutional', 'O(k·n·d²)', 'O(1)', 'O(log_k n)'],
    ['Self-Attention (restricted)', 'O(r·n·d)', 'O(1)', 'O(n/r)']
  ];
  s7.addTable(rows, {
    ...p7[0],
    colW: [1.55, 1.15, 1.0, 1.1],
    fontSize: 9.5,
    fontFace: 'Arial',
    border: { pt: 0.75, color: 'C9C6E8' },
    align: 'center',
    valign: 'middle',
    fill: { color: 'FFFFFF' }
  });

  // Slides 8-9
  await html2pptx('slides/08-training.html', pptx);
  await html2pptx('slides/09-results.html', pptx);

  // Slide 10: EN-DE BLEU bar chart (values from Table 2, p. 8)
  const { slide: s10, placeholders: p10 } = await html2pptx('slides/10-chart.html', pptx);
  s10.addChart(pptx.charts.BAR, [{
    name: 'BLEU',
    labels: ['ByteNet', 'GNMT+RL', 'ConvS2S', 'MoE', 'ConvS2S Ens.', 'TF (base)', 'TF (big)'],
    values: [23.75, 24.6, 25.16, 26.03, 26.36, 27.3, 28.4]
  }], {
    ...p10[0],
    barDir: 'col',
    showLegend: false,
    showValue: true,
    dataLabelPosition: 'outEnd',
    dataLabelFontSize: 9,
    dataLabelColor: '1A1633',
    dataLabelFormatCode: '0.00',
    showCatAxisTitle: false,
    catAxisLabelFontSize: 9,
    valAxisMinVal: 20,
    valAxisMaxVal: 30,
    valAxisMajorUnit: 2,
    showValAxisTitle: true,
    valAxisTitle: 'BLEU (newstest2014)',
    valAxisLabelFontSize: 8,
    valAxisTitleFontSize: 9,
    chartColors: ['9B97B8', '9B97B8', '9B97B8', '9B97B8', '7C3AED', '4338CA', 'F59E0B'],
    valAxisLineShow: false,
    serAxisLineShow: false,
    showCatName: true
  });

  // Slides 11-13
  await html2pptx('slides/11-generalization.html', pptx);
  await html2pptx('slides/12-interpretability.html', pptx);
  await html2pptx('slides/13-conclusion.html', pptx);

  await pptx.writeFile({ fileName: 'output/attention-is-all-you-need.pptx' });
  console.log('Saved output/attention-is-all-you-need.pptx');
}

build().catch(e => { console.error(e); process.exit(1); });

import { generateHTML } from './lib/template.js';

async function test() {
  const html1 = await generateHTML('# Hello\n\nThis is **bold** text.', 'template-tech');
  console.log('Test 1 - Bold text:');
  console.log(html1);
  console.log('Has strong tag:', html1.includes('<strong'));

  const html2 = await generateHTML('```javascript\nconst x = 1;\n```', 'template-tech');
  console.log('\nTest 2 - Code block:');
  console.log(html2);
  console.log('Has pre tag:', html2.includes('<pre'));
  console.log('Has code tag:', html2.includes('<code'));
}

test();

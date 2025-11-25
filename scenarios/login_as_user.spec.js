import { test, expect } from '@playwright/test';

test('test and capture page state', async ({ page }) => {
  await page.goto('http://localhost:3000');
  
  const pageState = {
    url: page.url(),
    title: await page.title(),
    visibleButtons: await page.locator('button:visible').allTextContents(),
    visibleInputs: await page.locator('input:visible, textarea:visible').count(),
    visibleLinks: await page.locator('a:visible').allTextContents(),
    headings: {
      h1: await page.locator('h1:visible').allTextContents(),
      h2: await page.locator('h2:visible').allTextContents(),
      h3: await page.locator('h3:visible').allTextContents(),
    },
    forms: await page.locator('form:visible').count(),
    images: await page.locator('img:visible').count(),
    interactiveElements: {
      buttons: await page.locator('button:visible, [role="button"]:visible').count(),
      inputs: await page.locator('input:visible, textarea:visible, select:visible').count(),
      links: await page.locator('a:visible').count(),
    },
    pageStructure: await page.evaluate(() => {
      const structure = {
        mainSections: [],
        navigation: [],
        content: [],
      };
      
      const main = document.querySelector('main');
      const nav = document.querySelector('nav');
      const header = document.querySelector('header');
      const footer = document.querySelector('footer');
      
      if (main) structure.mainSections.push('main');
      if (nav) structure.navigation.push('nav');
      if (header) structure.content.push('header');
      if (footer) structure.content.push('footer');
      
      return structure;
    }),
  };
  
  console.log('Page State:', JSON.stringify(pageState, null, 2));
  
  const selectors = await page.evaluate(() => {
    const elements = [];
    const interactive = document.querySelectorAll('button, a, input, textarea, select, [role="button"], [onclick]');
    
    interactive.forEach((el, index) => {
      if (el.offsetParent !== null) {
        const id = el.id ? `#${el.id}` : '';
        const classes = el.className ? `.${el.className.split(' ').join('.')}` : '';
        const tag = el.tagName.toLowerCase();
        const text = el.textContent?.trim().substring(0, 50) || '';
        const type = el.type || '';
        const role = el.getAttribute('role') || '';
        
        elements.push({
          index,
          tag,
          id,
          classes: classes.substring(0, 100),
          text,
          type,
          role,
          selector: id || (classes ? `${tag}${classes.split(' ')[0]}` : tag),
        });
      }
    });
    
    return elements;
  });
  
  console.log('Interactive Elements:', JSON.stringify(selectors, null, 2));

  await page.locator('input.form-control[type="text"]').fill('user');

  const additionalPageState = {
    url: page.url(),
    title: await page.title(),
    visibleButtons: await page.locator('button:visible').allTextContents(),
    visibleInputs: await page.locator('input:visible, textarea:visible').count(),
    visibleLinks: await page.locator('a:visible').allTextContents(),
    headings: {
      h1: await page.locator('h1:visible').allTextContents(),
      h2: await page.locator('h2:visible').allTextContents(),
      h3: await page.locator('h3:visible').allTextContents(),
    },
    forms: await page.locator('form:visible').count(),
    images: await page.locator('img:visible').count(),
    interactiveElements: {
      buttons: await page.locator('button:visible, [role="button"]:visible').count(),
      inputs: await page.locator('input:visible, textarea:visible, select:visible').count(),
      links: await page.locator('a:visible').count(),
    },
    pageStructure: await page.evaluate(() => {
      const structure = {
        mainSections: [],
        navigation: [],
        content: [],
      };
      
      const main = document.querySelector('main');
      const nav = document.querySelector('nav');
      const header = document.querySelector('header');
      const footer = document.querySelector('footer');
      
      if (main) structure.mainSections.push('main');
      if (nav) structure.navigation.push('nav');
      if (header) structure.content.push('header');
      if (footer) structure.content.push('footer');
      
      return structure;
    }),
  };
  
  console.log('Additional Page State:', JSON.stringify(additionalPageState, null, 2));
  
  const additionalSelectors = await page.evaluate(() => {
    const elements = [];
    const interactive = document.querySelectorAll('button, a, input, textarea, select, [role="button"], [onclick]');
    
    interactive.forEach((el, index) => {
      if (el.offsetParent !== null) {
        const id = el.id ? `#${el.id}` : '';
        const classes = el.className ? `.${el.className.split(' ').join('.')}` : '';
        const tag = el.tagName.toLowerCase();
        const text = el.textContent?.trim().substring(0, 50) || '';
        const type = el.type || '';
        const role = el.getAttribute('role') || '';
        
        elements.push({
          index,
          tag,
          id,
          classes: classes.substring(0, 100),
          text,
          type,
          role,
          selector: id || (classes ? `${tag}${classes.split(' ')[0]}` : tag),
        });
      }
    });
    
    return elements;
  });
  
  console.log('Additional Interactive Elements:', JSON.stringify(additionalSelectors, null, 2));

  await page.fill('input[type="password"]', 'password');

  const finalPageState = {
    url: page.url(),
    title: await page.title(),
    visibleButtons: await page.locator('button:visible').allTextContents(),
    visibleInputs: await page.locator('input:visible, textarea:visible').count(),
    visibleLinks: await page.locator('a:visible').allTextContents(),
    headings: {
      h1: await page.locator('h1:visible').allTextContents(),
      h2: await page.locator('h2:visible').allTextContents(),
      h3: await page.locator('h3:visible').allTextContents(),
    },
    forms: await page.locator('form:visible').count(),
    images: await page.locator('img:visible').count(),
    interactiveElements: {
      buttons: await page.locator('button:visible, [role="button"]:visible').count(),
      inputs: await page.locator('input:visible, textarea:visible, select:visible').count(),
      links: await page.locator('a:visible').count(),
    },
    pageStructure: await page.evaluate(() => {
      const structure = {
        mainSections: [],
        navigation: [],
        content: [],
      };
      
      const main = document.querySelector('main');
      const nav = document.querySelector('nav');
      const header = document.querySelector('header');
      const footer = document.querySelector('footer');
      
      if (main) structure.mainSections.push('main');
      if (nav) structure.navigation.push('nav');
      if (header) structure.content.push('header');
      if (footer) structure.content.push('footer');
      
      return structure;
    }),
  };
  
  console.log('Final Page State:', JSON.stringify(finalPageState, null, 2));
  
  const finalSelectors = await page.evaluate(() => {
    const elements = [];
    const interactive = document.querySelectorAll('button, a, input, textarea, select, [role="button"], [onclick]');
    
    interactive.forEach((el, index) => {
      if (el.offsetParent !== null) {
        const id = el.id ? `#${el.id}` : '';
        const classes = el.className ? `.${el.className.split(' ').join('.')}` : '';
        const tag = el.tagName.toLowerCase();
        const text = el.textContent?.trim().substring(0, 50) || '';
        const type = el.type || '';
        const role = el.getAttribute('role') || '';
        
        elements.push({
          index,
          tag,
          id,
          classes: classes.substring(0, 100),
          text,
          type,
          role,
          selector: id || (classes ? `${tag}${classes.split(' ')[0]}` : tag),
        });
      }
    });
    
    return elements;
  });
  
  console.log('Final Interactive Elements:', JSON.stringify(finalSelectors, null, 2));

  await page.fill('input.form-control[type="text"]', 'your_username');
  await page.fill('input.form-control[type="password"]', 'your_password');
  await page.click('button.btn.btn-primary');

  // Additional capture page state
  await page.goto('http://localhost:3000');
  
  const additionalPageStateCapture = {
    url: page.url(),
    title: await page.title(),
    visibleButtons: await page.locator('button:visible').allTextContents(),
    visibleInputs: await page.locator('input:visible, textarea:visible').count(),
    visibleLinks: await page.locator('a:visible').allTextContents(),
    headings: {
      h1: await page.locator('h1:visible').allTextContents(),
      h2: await page.locator('h2:visible').allTextContents(),
      h3: await page.locator('h3:visible').allTextContents(),
    },
    forms: await page.locator('form:visible').count(),
    images: await page.locator('img:visible').count(),
    interactiveElements: {
      buttons: await page.locator('button:visible, [role="button"]:visible').count(),
      inputs: await page.locator('input:visible, textarea:visible, select:visible').count(),
      links: await page.locator('a:visible').count(),
    },
    pageStructure: await page.evaluate(() => {
      const structure = {
        mainSections: [],
        navigation: [],
        content: [],
      };
      
      const main = document.querySelector('main');
      const nav = document.querySelector('nav');
      const header = document.querySelector('header');
      const footer = document.querySelector('footer');
      
      if (main) structure.mainSections.push('main');
      if (nav) structure.navigation.push('nav');
      if (header) structure.content.push('header');
      if (footer) structure.content.push('footer');
      
      return structure;
    }),
  };
  
  console.log('Additional Page State Capture:', JSON.stringify(additionalPageStateCapture, null, 2));
  
  const additionalSelectorsCapture = await page.evaluate(() => {
    const elements = [];
    const interactive = document.querySelectorAll('button, a, input, textarea, select, [role="button"], [onclick]');
    
    interactive.forEach((el, index) => {
      if (el.offsetParent !== null) {
        const id = el.id ? `#${el.id}` : '';
        const classes = el.className ? `.${el.className.split(' ').join('.')}` : '';
        const tag = el.tagName.toLowerCase();
        const text = el.textContent?.trim().substring(0, 50) || '';
        const type = el.type || '';
        const role = el.getAttribute('role') || '';
        
        elements.push({
          index,
          tag,
          id,
          classes: classes.substring(0, 100),
          text,
          type,
          role,
          selector: id || (classes ? `${tag}${classes.split(' ')[0]}` : tag),
        });
      }
    });
    
    return elements;
  });
  
  console.log('Additional Interactive Elements Capture:', JSON.stringify(additionalSelectorsCapture, null, 2));

  // Capture page state after additional actions
  await page.goto('http://localhost:3000');
  
  const finalPageStateCapture = {
    url: page.url(),
    title: await page.title(),
    visibleButtons: await page.locator('button:visible').allTextContents(),
    visibleInputs: await page.locator('input:visible, textarea:visible').count(),
    visibleLinks: await page.locator('a:visible').allTextContents(),
    headings: {
      h1: await page.locator('h1:visible').allTextContents(),
      h2: await page.locator('h2:visible').allTextContents(),
      h3: await page.locator('h3:visible').allTextContents(),
    },
    forms: await page.locator('form:visible').count(),
    images: await page.locator('img:visible').count(),
    interactiveElements: {
      buttons: await page.locator('button:visible, [role="button"]:visible').count(),
      inputs: await page.locator('input:visible, textarea:visible, select:visible').count(),
      links: await page.locator('a:visible').count(),
    },
    pageStructure: await page.evaluate(() => {
      const structure = {
        mainSections: [],
        navigation: [],
        content: [],
      };
      
      const main = document.querySelector('main');
      const nav = document.querySelector('nav');
      const header = document.querySelector('header');
      const footer = document.querySelector('footer');
      
      if (main) structure.mainSections.push('main');
      if (nav) structure.navigation.push('nav');
      if (header) structure.content.push('header');
      if (footer) structure.content.push('footer');
      
      return structure;
    }),
  };
  
  console.log('Final Page State Capture:', JSON.stringify(finalPageStateCapture, null, 2));
  
  const finalSelectorsCapture = await page.evaluate(() => {
    const elements = [];
    const interactive = document.querySelectorAll('button, a, input, textarea, select, [role="button"], [onclick]');
    
    interactive.forEach((el, index) => {
      if (el.offsetParent !== null) {
        const id = el.id ? `#${el.id}` : '';
        const classes = el.className ? `.${el.className.split(' ').join('.')}` : '';
        const tag = el.tagName.toLowerCase();
        const text = el.textContent?.trim().substring(0, 50) || '';
        const type = el.type || '';
        const role = el.getAttribute('role') || '';
        
        elements.push({
          index,
          tag,
          id,
          classes: classes.substring(0, 100),
          text,
          type,
          role,
          selector: id || (classes ? `${tag}${classes.split(' ')[0]}` : tag),
        });
      }
    });
    
    return elements;
  });
  
  console.log('Final Interactive Elements Capture:', JSON.stringify(finalSelectorsCapture, null, 2));

  await page.click('button.btn.btn-primary');
  await expect(page).toHaveURL(/.*dashboard/);
});
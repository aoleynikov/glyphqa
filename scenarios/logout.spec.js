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

  await page.locator('input.form-control[type="text"]').fill('your_username'); // Replace 'your_username' with the actual username
  await page.locator('input.form-control[type="password"]').fill('your_password'); // Replace 'your_password' with the actual password
  await page.locator('button.btn.btn-primary').click();

  await page.goto('http://localhost:3000');
  
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

  const loginButton = page.locator('button.btn.btn-primary');
  await loginButton.click();

  const userProfile = page.locator('selector-for-user-profile'); // Replace with actual selector for user profile
  await expect(userProfile).toBeVisible(); // Check if user is logged in before logging out

  await page.goto('http://localhost:3000');
  
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

  const logoutButton = page.locator('selector-for-logout-button'); // Replace with actual selector for logout button
  await logoutButton.click();

  await page.goto('http://localhost:3000');
  
  const additionalPageState2 = {
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
  
  console.log('Additional Page State:', JSON.stringify(additionalPageState2, null, 2));
  
  const additionalSelectors2 = await page.evaluate(() => {
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
  
  console.log('Additional Interactive Elements:', JSON.stringify(additionalSelectors2, null, 2));

  await page.goto('http://localhost:3000');
  
  const pageState2 = {
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
  
  console.log('Page State:', JSON.stringify(pageState2, null, 2));
  
  const selectors2 = await page.evaluate(() => {
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
  
  console.log('Interactive Elements:', JSON.stringify(selectors2, null, 2));

  const logoutButton = page.locator('selector-for-logout-button'); // Replace with actual selector for logout button
  await logoutButton.click(); // Click the logout button
  await expect(page).toHaveURL('http://localhost:3000/login'); // Check if redirected to the login form
  await expect(page.locator('selector-for-login-form')).toBeVisible(); // Check if the login form is visible
});
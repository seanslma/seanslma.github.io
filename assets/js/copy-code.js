document.addEventListener("DOMContentLoaded", function() {
    document.querySelectorAll('div.highlighter-rouge').forEach(block => {
      const button = document.createElement('button');
      button.innerText = 'Copy';
      button.className = 'copy-button';
      block.style.position = 'relative';
      button.addEventListener('click', async () => {
        const code = block.querySelector('pre').innerText;
        try {
          await navigator.clipboard.writeText(code);
          button.innerText = 'Copied!';
          setTimeout(() => (button.innerText = 'Copy'), 2000);
        } catch (err) {
          console.error('Failed to copy: ', err);
        }
      });
      block.appendChild(button);
    });
  });

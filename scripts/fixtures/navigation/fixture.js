export function mount(main) {
  const button = main.querySelector('#fixture-action');
  const output = main.querySelector('#fixture-count');
  const click = () => { output.textContent = String(Number(output.textContent) + 1); };
  button.addEventListener('click', click);
  return () => button.removeEventListener('click', click);
}

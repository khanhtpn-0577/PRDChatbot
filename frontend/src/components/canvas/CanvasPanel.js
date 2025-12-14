export function renderCanvasPanel(container, state) {
  if (!state.hasSRS) {
    container.innerHTML = `
      <div class="text-gray-400 italic">
        SRS sẽ được tạo sau prompt đầu tiên...
      </div>
    `;
    return;
  }

  container.innerHTML = `
    <textarea
      class="w-full h-full resize-none border rounded-lg p-4 text-sm leading-relaxed font-mono bg-white focus:outline-none"
    >${state.srsContent}</textarea>
  `;
}

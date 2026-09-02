const experiences = {
  'ca-inter-sep26': {
    title: 'CA Inter Sep ’26 Exam Strategy',
    src: 'public/experiences/ca-inter-sep26/index.html'
  },
  'ca-foundation-sep26': {
    title: 'CA Foundation Sep ’26 Exam Strategy',
    src: 'public/experiences/ca-foundation-sep26/index.html'
  },
  'bucket-0': {
    title: 'Daily Habits · Bucket 0',
    src: 'public/experiences/bucket-0/index.html'
  },
  'teaching-style': {
    title: 'Pranav Sir’s Teaching Method',
    src: 'public/experiences/teaching-style/index.html'
  },
  'kahaani': {
    title: 'Kahaani · Concept Book Animations',
    src: 'public/experiences/kahaani/index.html'
  },
  'koncept': {
    title: 'Koncept · Layer 2 Revision',
    src: 'public/experiences/koncept/index.html'
  }
};

const params = new URLSearchParams(window.location.search);
const experience = experiences[params.get('experience')];
const frame = document.querySelector('#experience-frame');
const title = document.querySelector('#experience-title');
const error = document.querySelector('#viewer-error');
const fullscreenButton = document.querySelector('#fullscreen-button');

if (!experience) {
  frame.hidden = true;
  error.hidden = false;
} else {
  title.textContent = experience.title;
  document.title = `${experience.title} | CA Pranav`;
  frame.src = experience.src;
}

fullscreenButton.addEventListener('click', async () => {
  if (!document.fullscreenElement) {
    await frame.requestFullscreen();
  } else {
    await document.exitFullscreen();
  }
});

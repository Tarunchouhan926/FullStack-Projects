document.addEventListener("DOMContentLoaded", () => {
    const scoreCircle = document.querySelector(".score-circle");
    const score = parseInt(scoreCircle.getAttribute("data-score"));
    const angle = Math.min(score, 100) * 3.6;

    const gradient = `conic-gradient(#4f46e5 ${angle}deg, #d1d5db 0deg)`;
    scoreCircle.style.setProperty('--dynamic-score', gradient);
});

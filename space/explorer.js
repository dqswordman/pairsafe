"use strict";
const element = (id) => document.getElementById(id);
const model = element("model");
const threshold = element("threshold");
let models;

function showCounts() {
  const [theta, both, safe, unsafe] = models[model.value].rows[Number(threshold.value)];
  element("theta").textContent = theta.toFixed(4);
  threshold.setAttribute("aria-valuetext", theta.toFixed(4));
  for (const [id, count] of [["paired", both], ["safe", safe], ["unsafe", unsafe]]) {
    element(id).textContent = count + " / 150";
  }
}

function useModel() {
  const selected = models[model.value];
  threshold.max = selected.rows.length - 1;
  threshold.value = selected.oracle_index;
  showCounts();
}

async function start() {
  const response = await fetch("thresholds.json");
  if (!response.ok) throw new Error("Could not load the score summary.");
  models = await response.json();
  model.addEventListener("change", useModel);
  threshold.addEventListener("input", showCounts);
  element("best").addEventListener("click", useModel);
  useModel();
  element("status").hidden = true;
  element("controls").hidden = false;
}

start().catch(() => {
  element("status").textContent = "The interactive data could not be loaded. The published counts and downloadable release are available below.";
});

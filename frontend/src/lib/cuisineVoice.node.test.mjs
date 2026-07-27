/**
 * Node test runner (no jest): node --test src/lib/cuisineVoice.node.test.mjs
 * Keep in sync with cuisineVoice.ts normalize/parse logic.
 */
import { describe, it } from "node:test";
import assert from "node:assert/strict";

function normalize(raw) {
  return raw
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-z0-9\s]/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function parseCuisineVoiceCommand(raw) {
  const t = normalize(raw);
  if (!t) return "unknown";
  if (
    /\b(suivant|next|avance|apres|continuer|continue|ok suivant)\b/.test(t) ||
    t === "suivant" ||
    t === "next"
  ) {
    return "next";
  }
  if (/\b(precedent|retour|avant|back|previous)\b/.test(t) || t === "retour") {
    return "prev";
  }
  if (/\b(repete|repeat|encore|redis|relire)\b/.test(t) || t === "repete") {
    return "repeat";
  }
  if (/\b(pause|stop|arrete|reprendre|resume)\b/.test(t)) {
    return "pause";
  }
  return "unknown";
}

describe("parseCuisineVoiceCommand", () => {
  it("maps next variants", () => {
    assert.equal(parseCuisineVoiceCommand("Suivant !"), "next");
    assert.equal(parseCuisineVoiceCommand("ok next"), "next");
    assert.equal(parseCuisineVoiceCommand("avance s'il te plaît"), "next");
  });
  it("maps prev / repeat / pause", () => {
    assert.equal(parseCuisineVoiceCommand("précédent"), "prev");
    assert.equal(parseCuisineVoiceCommand("répète"), "repeat");
    assert.equal(parseCuisineVoiceCommand("pause minuteur"), "pause");
  });
  it("unknown on noise", () => {
    assert.equal(parseCuisineVoiceCommand("bonjour le riz"), "unknown");
  });
});

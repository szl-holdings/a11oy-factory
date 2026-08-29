import unittest

from a11oy_factory.cells import ADMITTED, FRONTIERS, LYTE
from a11oy_factory.compiler import BLOCKED, compile_cell
from a11oy_factory.jobs import JOBS, search_jobs


class CompilerTests(unittest.TestCase):
    def test_lyte_is_the_only_admitted_cell(self):
        self.assertEqual(ADMITTED, frozenset({"lyte"}))
        rec = compile_cell("lyte", signal="bind as a11oy package")
        self.assertEqual(rec.decision, "ALLOW")
        self.assertEqual(rec.bind, "BIND_AS_A11OY_PACKAGE")
        self.assertEqual(rec.flagship, "a11oy")
        self.assertEqual(rec.signer, "UNSIGNED-honest")
        self.assertIsNone(rec.energy)
        self.assertEqual(len(rec.hash), 64)

    def test_frontiers_are_named_and_blocked_roadmap(self):
        self.assertEqual(len(FRONTIERS), 25)
        expected = {
            "N1": "Serve",
            "N2": "Graph",
            "N3": "Guard",
            "N4": "Mosaic",
            "N5": "Lattice",
            "N6": "Cover",
            "N7": "Quant",
            "N8": "Title",
            "N9": "Retrieve",
            "N10": "Observe",
            "N11": "Tune",
            "N12": "Schema",
            "N13": "Energy",
            "N14": "Tool",
            "N15": "Memory",
            "N16": "Eval",
            "N17": "Mesh",
            "N18": "Route",
            "N19": "Cache",
            "N20": "Voice",
            "N21": "Sandbox",
            "N22": "Identity",
            "N23": "Rails",
            "N24": "Browser",
            "N25": "Policy",
        }
        for cell in FRONTIERS:
            self.assertEqual(cell.title, expected[cell.id])
            self.assertFalse(cell.admitted)
            self.assertTrue(cell.cite)
            self.assertTrue(cell.szl)
            rec = compile_cell(cell.id)
            self.assertEqual(rec.decision, BLOCKED)
            if cell.id == "N13":
                self.assertEqual(rec.honesty_tier, "UNAVAILABLE")
            else:
                self.assertEqual(rec.honesty_tier, "ROADMAP")
            self.assertIn(cell.title, rec.note)

    def test_unknown_fails_closed(self):
        rec = compile_cell("not-a-cell")
        self.assertEqual(rec.decision, BLOCKED)
        self.assertEqual(rec.honesty_tier, "UNAVAILABLE")

    def test_empty_fails_closed(self):
        rec = compile_cell("")
        self.assertEqual(rec.decision, BLOCKED)

    def test_lambda_never_proven(self):
        rec = compile_cell("lyte")
        self.assertEqual(rec.lambda_status, "Conjecture 1")

    def test_search_cites_leaders_and_refuses_rehost(self):
        vllm = search_jobs("vllm")
        self.assertTrue(vllm["jobs"])
        self.assertEqual(vllm["jobs"][0]["leader"], "vLLM")
        self.assertIn("Do not rehost", vllm["jobs"][0]["refuse"])
        self.assertEqual(vllm["cells"][0]["id"], "N1")
        self.assertFalse(vllm["cells"][0]["admitted"])

        graph = search_jobs("langgraph")
        self.assertEqual(graph["jobs"][0]["cell"], "N2")

        guard = search_jobs("llama guard")
        self.assertEqual(guard["jobs"][0]["cell"], "N3")

        cover = search_jobs("guidewire")
        self.assertEqual(cover["jobs"][0]["cell"], "N6")

        retrieve = search_jobs("llamaindex")
        self.assertEqual(retrieve["jobs"][0]["cell"], "N9")
        self.assertFalse(retrieve["jobs"][0]["admitted"])

        observe = search_jobs("phoenix")
        self.assertEqual(observe["jobs"][0]["cell"], "N10")

        tune = search_jobs("unsloth")
        self.assertEqual(tune["jobs"][0]["cell"], "N11")

        schema = search_jobs("outlines")
        self.assertEqual(schema["jobs"][0]["cell"], "N12")

        energy_cell = search_jobs("nvml")
        self.assertTrue(any(c["id"] == "N13" for c in energy_cell["cells"]))

        tool = search_jobs("mcp")
        self.assertEqual(tool["jobs"][0]["cell"], "N14")
        self.assertIn("Do not rehost", tool["jobs"][0]["refuse"])

        memory = search_jobs("mem0")
        self.assertEqual(memory["jobs"][0]["cell"], "N15")

        ev = search_jobs("ragas")
        self.assertEqual(ev["jobs"][0]["cell"], "N16")

        mesh = search_jobs("dynamo")
        self.assertEqual(mesh["jobs"][0]["cell"], "N17")

        route = search_jobs("litellm")
        self.assertEqual(route["jobs"][0]["cell"], "N18")
        self.assertIn("Do not rehost", route["jobs"][0]["refuse"])

        cache = search_jobs("lmcache")
        self.assertEqual(cache["jobs"][0]["cell"], "N19")

        voice = search_jobs("livekit")
        self.assertEqual(voice["jobs"][0]["cell"], "N20")

        sand = search_jobs("daytona")
        self.assertEqual(sand["jobs"][0]["cell"], "N21")

        ident = search_jobs("spiffe")
        self.assertEqual(ident["jobs"][0]["cell"], "N22")
        self.assertIn("Do not rehost", ident["jobs"][0]["refuse"])

        rails = search_jobs("nemo")
        self.assertEqual(rails["jobs"][0]["cell"], "N23")

        browser = search_jobs("playwright")
        self.assertEqual(browser["jobs"][0]["cell"], "N24")

        policy = search_jobs("cedar")
        self.assertEqual(policy["jobs"][0]["cell"], "N25")

        sig = search_jobs("sigstore")
        self.assertEqual(sig["jobs"][0]["honesty"], "STRUCTURAL-ONLY")
        self.assertEqual(sig["jobs"][0]["cell"], "")

        energy = search_jobs("electricity")
        self.assertEqual(energy["jobs"][0]["honesty"], "UNAVAILABLE")
        self.assertIsNone(energy["energy"])

    def test_search_empty_returns_catalog(self):
        all_jobs = search_jobs("")
        self.assertGreaterEqual(len(all_jobs["jobs"]), len(JOBS))
        self.assertEqual(LYTE.id, "lyte")

    def test_typo_tolerant_cell_ids(self):
        rec = compile_cell("n1")
        self.assertEqual(rec.cell, "N1")
        self.assertEqual(rec.decision, BLOCKED)
        rec = compile_cell("serve")
        self.assertEqual(rec.cell, "N1")
        rec = compile_cell("retrive")
        self.assertEqual(rec.cell, "N9")
        self.assertEqual(rec.decision, BLOCKED)
        rec = compile_cell("n12")
        self.assertEqual(rec.cell, "N12")
        self.assertEqual(rec.decision, BLOCKED)
        rec = compile_cell("energy")
        self.assertEqual(rec.cell, "N13")
        self.assertEqual(rec.decision, BLOCKED)
        self.assertEqual(rec.honesty_tier, "UNAVAILABLE")
        rec = compile_cell("mcp")
        self.assertEqual(rec.cell, "N14")
        self.assertEqual(rec.decision, BLOCKED)
        rec = compile_cell("mem0")
        self.assertEqual(rec.cell, "N15")
        rec = compile_cell("eval")
        self.assertEqual(rec.cell, "N16")
        rec = compile_cell("dynamo")
        self.assertEqual(rec.cell, "N17")
        self.assertEqual(rec.decision, BLOCKED)
        rec = compile_cell("litellm")
        self.assertEqual(rec.cell, "N18")
        rec = compile_cell("lmcache")
        self.assertEqual(rec.cell, "N19")
        rec = compile_cell("livekit")
        self.assertEqual(rec.cell, "N20")
        rec = compile_cell("daytona")
        self.assertEqual(rec.cell, "N21")
        self.assertEqual(rec.decision, BLOCKED)
        rec = compile_cell("spiffe")
        self.assertEqual(rec.cell, "N22")
        rec = compile_cell("nemo")
        self.assertEqual(rec.cell, "N23")
        rec = compile_cell("playwright")
        self.assertEqual(rec.cell, "N24")
        rec = compile_cell("cedar")
        self.assertEqual(rec.cell, "N25")
        self.assertEqual(rec.decision, BLOCKED)

    def test_typo_tolerant_search(self):
        vlm = search_jobs("vlm")
        self.assertTrue(vlm["jobs"])
        self.assertEqual(vlm["jobs"][0]["leader"], "vLLM")
        rag = search_jobs("rag")
        self.assertTrue(any(j["cell"] == "N9" for j in rag["jobs"]))
        qlora = search_jobs("qlora")
        self.assertEqual(qlora["jobs"][0]["cell"], "N11")
        retrive = search_jobs("retrive")
        self.assertTrue(any(c["id"] == "N9" for c in retrive["cells"]))


if __name__ == "__main__":
    unittest.main()

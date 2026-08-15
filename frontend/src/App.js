import "@/App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Layout from "@/components/Layout";
import Home from "@/pages/Home";
import Talk from "@/pages/Talk";
import DreamOffer from "@/pages/DreamOffer";
import People from "@/pages/People";
import Memory from "@/pages/Memory";
import Calendar from "@/pages/Calendar";
import Knowledge from "@/pages/Knowledge";
import Reflection from "@/pages/Reflection";
import Stories from "@/pages/Stories";
import More from "@/pages/More";

function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/talk" element={<Talk />} />
          <Route path="/dream-offer" element={<DreamOffer />} />
          <Route path="/people" element={<People />} />
          <Route path="/memory" element={<Memory />} />
          <Route path="/calendar" element={<Calendar />} />
          <Route path="/knowledge" element={<Knowledge />} />
          <Route path="/reflection" element={<Reflection />} />
          <Route path="/stories" element={<Stories />} />
          <Route path="/more" element={<More />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}

export default App;

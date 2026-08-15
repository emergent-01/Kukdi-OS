import { useEffect, useState } from "react";
import { Plus, Trash2 } from "lucide-react";
import { api } from "../lib/api";
import { Modal, Field, inputClass, PrimaryButton } from "../components/Modal";

export default function People() {
  const [people, setPeople] = useState([]);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({ name: "", relation: "", company: "", birthday: "", notes: "" });

  const load = () => api.people().then((d) => setPeople(d.people || []));
  useEffect(() => { load(); }, []);

  const add = async () => {
    if (!form.name.trim()) return;
    await api.createPerson(form);
    setOpen(false);
    setForm({ name: "", relation: "", company: "", birthday: "", notes: "" });
    load();
  };

  return (
    <div data-testid="people-page">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs tracking-[0.18em] uppercase text-[#8A8F8C]">People</span>
        <button onClick={() => setOpen(true)} data-testid="add-person-btn" className="flex items-center gap-1.5 text-sm text-[#5C605A] hover:text-[#2C2D2B] transition-colors">
          <Plus size={15} strokeWidth={1.5} /> Add
        </button>
      </div>
      <h1 className="font-editorial text-5xl md:text-6xl text-[#2C2D2B] mb-12">The people who matter</h1>

      <div className="space-y-12">
        {people.map((p) => (
          <div key={p.id} className="flex gap-6 group" data-testid={`person-${p.id}`}>
            <div className="h-14 w-14 rounded-full bg-[#D4DDD7] shrink-0 flex items-center justify-center font-editorial text-2xl text-[#2C2D2B]">
              {p.name.charAt(0)}
            </div>
            <div className="flex-1 border-b border-[#E2DFD8] pb-10">
              <div className="flex items-baseline justify-between">
                <h3 className="font-editorial text-3xl text-[#2C2D2B]">{p.name}</h3>
                <button
                  onClick={async () => { await api.deletePerson(p.id); load(); }}
                  data-testid={`person-delete-${p.id}`}
                  className="opacity-0 group-hover:opacity-100 transition-opacity text-[#8A8F8C] hover:text-[#a9564a]"
                >
                  <Trash2 size={15} strokeWidth={1.5} />
                </button>
              </div>
              <p className="text-sm text-[#8A8F8C] mt-1">
                {[p.relation, p.company, p.birthday && `🎂 ${p.birthday}`].filter(Boolean).join(" · ")}
              </p>
              {p.notes && <p className="text-[#5C605A] mt-4 leading-relaxed max-w-xl">{p.notes}</p>}
              {p.important?.length > 0 && (
                <ul className="mt-4 space-y-1.5">
                  {p.important.map((it, i) => (
                    <li key={i} className="flex items-center gap-2.5 text-[#5C605A]">
                      <span className="h-1 w-1 rounded-full bg-[#9DB0A3]" />
                      {it}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        ))}
      </div>

      <Modal open={open} onClose={() => setOpen(false)} title="Add a person" testId="person-modal">
        <Field label="Name"><input className={inputClass} value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} data-testid="person-name-input" /></Field>
        <Field label="Relationship"><input className={inputClass} value={form.relation} onChange={(e) => setForm({ ...form, relation: e.target.value })} data-testid="person-relation-input" /></Field>
        <Field label="Company"><input className={inputClass} value={form.company} onChange={(e) => setForm({ ...form, company: e.target.value })} data-testid="person-company-input" /></Field>
        <Field label="Birthday"><input className={inputClass} value={form.birthday} onChange={(e) => setForm({ ...form, birthday: e.target.value })} data-testid="person-birthday-input" /></Field>
        <Field label="Notes"><textarea className={inputClass} rows={3} value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} data-testid="person-notes-input" /></Field>
        <PrimaryButton onClick={add} data-testid="person-save-btn">Add person</PrimaryButton>
      </Modal>
    </div>
  );
}

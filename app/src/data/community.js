export const regions = [
  "Dordrecht",
  "Rotterdam",
  "Antwerp",
  "Brussels",
  "Ghent",
  "Utrecht",
  "Liège",
  "Luxembourg City",
  "Groningen",
  "Eindhoven",
];

export const helpOptions = [
  { id: "survey", label: "Field surveys" },
  { id: "restore", label: "Habitat restoration" },
  { id: "report", label: "Citizen reports" },
  { id: "donate", label: "Local funding" },
];

export const opportunities = [
  {
    id: "wetlands",
    title: "Reconnect the wetlands",
    place: "Biesbosch",
    when: "Sat 26 Sep · 09:00",
    need: "8 survey volunteers",
    spots: 3,
    help: "survey",
  },
  {
    id: "shoreline",
    title: "Restore the shoreline",
    place: "Haringvliet",
    when: "Sun 27 Sep · 10:30",
    need: "Planting crew",
    spots: 5,
    help: "restore",
  },
  {
    id: "corridor",
    title: "Rewild the river corridor",
    place: "Oude Maas",
    when: "Wed 30 Sep · 16:00",
    need: "Bank mapping",
    spots: 4,
    help: "survey",
  },
  {
    id: "zwin",
    title: "Count migratory geese",
    place: "Zwin and Scheldt",
    when: "Sat 3 Oct · 07:30",
    need: "Dawn observers",
    spots: 6,
    help: "survey",
  },
  {
    id: "kempen",
    title: "Open heath pans",
    place: "Kempen",
    when: "Sat 10 Oct · 09:00",
    need: "Toad-pool crew",
    spots: 7,
    help: "restore",
  },
  {
    id: "ardennes",
    title: "Beaver bank survey",
    place: "Ourthe valley",
    when: "Sun 11 Oct · 11:00",
    need: "Track recorders",
    spots: 4,
    help: "survey",
  },
];

export const people = [
  { id: "am", name: "Alex Morgan", place: "Dordrecht", role: "Survey lead", hours: 42, status: "Active" },
  { id: "sl", name: "Sofie Lauwers", place: "Antwerp", role: "Citizen reporter", hours: 18, status: "Active" },
  { id: "jb", name: "Joris Bekker", place: "Rotterdam", role: "Restoration crew", hours: 31, status: "Active" },
  { id: "nw", name: "Noor Willems", place: "Utrecht", role: "Donor organiser", hours: 12, status: "Away" },
  { id: "km", name: "Koen Martens", place: "Ghent", role: "Water sampling", hours: 27, status: "Active" },
  { id: "el", name: "Elena Rossi", place: "Liège", role: "Beaver watch", hours: 22, status: "Active" },
  { id: "pt", name: "Pieter Theunissen", place: "Eindhoven", role: "Heath volunteer", hours: 16, status: "New" },
  { id: "mh", name: "Marie Hoffmann", place: "Luxembourg City", role: "Mine-pool steward", hours: 9, status: "New" },
  { id: "tv", name: "Tessa de Vries", place: "Groningen", role: "Eel survey", hours: 35, status: "Active" },
  { id: "ab", name: "Anouk Berger", place: "Brussels", role: "Forest walks", hours: 14, status: "Active" },
  { id: "fd", name: "Faisal Rahman", place: "Dordrecht", role: "Photo reports", hours: 8, status: "New" },
  { id: "lc", name: "Lotte Claessens", place: "Ghent", role: "Weekend planting", hours: 21, status: "Active" },
  { id: "hv", name: "Hanne Visser", place: "Rotterdam", role: "Reed planting", hours: 19, status: "Active" },
  { id: "bd", name: "Bram De Smet", place: "Antwerp", role: "Eel monitoring", hours: 24, status: "Active" },
  { id: "il", name: "Ines Lambert", place: "Brussels", role: "Citizen reporter", hours: 11, status: "New" },
  { id: "yj", name: "Yara Jansen", place: "Utrecht", role: "Dawn observer", hours: 17, status: "Active" },
  { id: "mk", name: "Milan Kovač", place: "Liège", role: "Bank mapping", hours: 15, status: "Active" },
  { id: "sg", name: "Sanne Groen", place: "Groningen", role: "Seal watch", hours: 28, status: "Active" },
  { id: "ow", name: "Olivier Wouters", place: "Ghent", role: "Creek steward", hours: 13, status: "New" },
  { id: "cp", name: "Chiara Pauwels", place: "The Hague", role: "Survey lead", hours: 33, status: "Active" },
  { id: "tn", name: "Thijs Noyens", place: "Eindhoven", role: "Heath volunteer", hours: 20, status: "Active" },
  { id: "af", name: "Amina Farouk", place: "Dordrecht", role: "Photo reports", hours: 9, status: "New" },
  { id: "rk", name: "Roos Kuiper", place: "Rotterdam", role: "Water sampling", hours: 22, status: "Active" },
  { id: "dv", name: "Daan Vermeulen", place: "Antwerp", role: "Planting crew", hours: 18, status: "Active" },
  { id: "lh", name: "Léa Hubert", place: "Luxembourg City", role: "River walks", hours: 14, status: "Active" },
  { id: "js", name: "Jonas Smeets", place: "Maastricht", role: "Toad-pool crew", hours: 16, status: "Active" },
  { id: "em", name: "Eva Meijer", place: "Haarlem", role: "Nest counts", hours: 25, status: "Active" },
  { id: "pb", name: "Pieter Bos", place: "Leiden", role: "Quiet-shore patrol", hours: 12, status: "New" },
  { id: "nl", name: "Nora Lindemans", place: "Leuven", role: "Forest walks", hours: 21, status: "Active" },
  { id: "gt", name: "Gert Timmermans", place: "Tilburg", role: "Weekend planting", hours: 10, status: "New" },
  { id: "fs", name: "Fien Schouten", place: "Delft", role: "Lab support", hours: 27, status: "Active" },
  { id: "wc", name: "Wout Claeys", place: "Bruges", role: "Mudflat watch", hours: 15, status: "Active" },
];

export const partners = [
  { id: "dwt", name: "Delta Wildlife Trust", type: "NGO", place: "Dordrecht", focus: "Wetlands", people: 28 },
  { id: "sh", name: "South Holland Nature Desk", type: "Municipality", place: "The Hague", focus: "Planning", people: 14 },
  { id: "tu", name: "TU Delft Water Lab", type: "University", place: "Delft", focus: "Monitoring", people: 11 },
  { id: "natuur", name: "Natuurpunt Scheldt", type: "NGO", place: "Antwerp", focus: "Birds", people: 22 },
  { id: "gent", name: "Stad Gent Groen", type: "Municipality", place: "Ghent", focus: "Creeks", people: 9 },
  { id: "uliege", name: "ULiège Ecology", type: "University", place: "Liège", focus: "Beavers", people: 8 },
  { id: "natur", name: "natur&ëmwelt", type: "NGO", place: "Luxembourg City", focus: "Rivers", people: 12 },
  { id: "port", name: "Port of Rotterdam Ecology", type: "Company", place: "Rotterdam", focus: "Shoreline", people: 6 },
  { id: "kempen", name: "Kempen Landschap", type: "NGO", place: "Turnhout", focus: "Heath", people: 17 },
  { id: "wadden", name: "Waddenvereniging", type: "NGO", place: "Groningen", focus: "Seals", people: 19 },
];

export const seedActivity = [
  { icon: "radio", tone: "amber", title: "Possible discharge near Dordrecht", detail: "Citizen photo + location · Awaiting verification", time: "12m ago" },
  { icon: "hand-heart", tone: "", title: "Wetland restoration reaches 82% funding", detail: "€4,200 added by 18 local donors", time: "48m ago" },
  { icon: "users", tone: "", title: "Saturday’s river survey is fully staffed", detail: "24 volunteers · 3 partner organisations", time: "2h ago" },
  { icon: "sprout", tone: "", title: "Haringvliet planting beds marked out", detail: "Delta Wildlife Trust · 40 reed bundles staged", time: "3h ago" },
  { icon: "bird", tone: "", title: "Zwin goose count logged 1,240 birds", detail: "Natuurpunt Scheldt · dawn shift complete", time: "5h ago" },
  { icon: "waves", tone: "", title: "Oude Maas temperature check posted", detail: "TU Delft Water Lab · 16.4 °C", time: "Yesterday" },
  { icon: "trees", tone: "", title: "Kempen heath pans scraped", detail: "7 volunteers · 3 new toad pools", time: "Yesterday" },
  { icon: "handshake", tone: "", title: "natur&ëmwelt joined the Sûre corridor", detail: "Partner agreement signed for autumn surveys", time: "2d ago" },
];

export const seedReports = [
  { id: "r1", place: "Dordrecht harbour edge", note: "Iridescent sheen on slack water, photo attached.", status: "Awaiting verification", who: "Sofie Lauwers", time: "12m ago" },
  { id: "r2", place: "Haringvliet spit", note: "Seal haul-out disturbed by three jet-skis.", status: "Field check assigned", who: "Joris Bekker", time: "3h ago" },
  { id: "r3", place: "Oude Maas km 12", note: "Collapsed bank exposing willow roots.", status: "Verified", who: "Alex Morgan", time: "Yesterday" },
  { id: "r4", place: "Zwin mudflat north", note: "New scrape looks good for avocet roost.", status: "Verified", who: "Anouk Berger", time: "2d ago" },
  { id: "r5", place: "Minett terrace pools", note: "Two pans already dry after last week’s fill.", status: "Needs action", who: "Marie Hoffmann", time: "3d ago" },
];

export const initials = (name) =>
  name
    .split(" ")
    .map((part) => part[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();

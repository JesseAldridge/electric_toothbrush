package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io/ioutil"
	"log"
	"net/http"
	"os"
	"os/exec"
	"os/user"
	"path/filepath"
	"time"

	"github.com/gdamore/tcell"
	"github.com/rivo/tview"
)


func run(cmd_tokens []string) error {
	log.Println("running:", cmd_tokens)
	cmd := exec.Command(cmd_tokens[0], cmd_tokens[1:]...)
	cmd.Stdin = os.Stdin
	cmd.Stdout = os.Stdout
	return cmd.Run()
}

func open_note(
	note_name string,
	dir_path string,
) {
	file_path := filepath.Join(dir_path, note_name) + ".txt"
	f, _ := os.OpenFile(file_path, os.O_CREATE, 0666) // create file if it doesn't exist
	f.Close()

	editor := os.Getenv("EDITOR")
	if editor == "" {
		err := run([]string{"open", file_path})
		if err != nil {
			run([]string{"open", "-e", file_path})
		}
	}
}

type post_type func(string, interface{}, interface{})

func post_to(
	host string,
	port int,
	endpoint string,
	payload interface{},
	result interface{},
) {
	payload_bytes, _ := json.Marshal(payload)
	url := fmt.Sprintf("http://%s:%d/%s", host, port, endpoint)
	start := time.Now()
	resp, err := http.Post(url, "application/json", bytes.NewBuffer(payload_bytes))
	log.Println("post time:", time.Now().Sub(start))
	if err != nil {
		log.Fatalln(err)
	}

	resp_json, err := ioutil.ReadAll(resp.Body)
	log.Println("response:", string(resp_json[:]))
	if err != nil {
		log.Fatalln(err)
	}
	if result != nil {
		err = json.Unmarshal(resp_json, result)
		if err != nil {
			log.Fatalln(err)
		}
	}
}

type SearchPayload struct {
	Query         string `json:"query"`
	SelectedIndex int    `json:"selected_index"`
}

type SearchResult struct {
	IsMore          bool      `json:"is_more"`
	MatchedNames    []string  `json:"matched_basenames"`
	Scores          []float64 `json:"scores"`
	SelectedContent string    `json:"selected_content"`
	SelectedName    string
}

type UI struct {
	Table    *tview.Table
	TextView *tview.TextView
}

func search_for(search_payload *SearchPayload, search_result *SearchResult, post post_type, ui UI) {
	search_result.SelectedContent = ""
	post("search", search_payload, search_result)

	if len(search_result.MatchedNames) > 9 {
		search_result.MatchedNames = search_result.MatchedNames[:9]
	}

	name_match := false
	for _, note_name := range search_result.MatchedNames {
		if note_name == search_payload.Query {
			name_match = true
			break
		}
	}
	if !name_match && search_payload.Query != "" {
		search_result.MatchedNames = append(
			search_result.MatchedNames,
			search_payload.Query+" [Create New Note]",
		)
	}

	if search_payload.SelectedIndex >= len(search_result.MatchedNames) {
		search_payload.SelectedIndex = 0
	}

	log.Println("search_payload.SelectedIndex:", search_payload.SelectedIndex)

	if len(search_result.MatchedNames) == 0 {
		search_result.SelectedName = ""
	} else if search_payload.SelectedIndex < len(search_result.MatchedNames)-1 {
		search_result.SelectedName = search_result.MatchedNames[search_payload.SelectedIndex]
	} else {
		search_result.SelectedName = search_payload.Query
	}

	render_ui(ui, search_payload, search_result)
}

func render_ui(ui UI, search_payload *SearchPayload, search_result *SearchResult) {
	ui.Table.Clear()
	for r, note_name := range search_result.MatchedNames {
		ui.Table.SetCell(r, 0, tview.NewTableCell(note_name))
	}
	ui.Table.Select(search_payload.SelectedIndex, 0)
	ui.TextView.SetText(search_result.SelectedContent)
	ui.TextView.ScrollToBeginning()
}

func main() {
	host := "localhost"
	port := 38906

	usr, _ := user.Current()
	dir_path := filepath.Join(usr.HomeDir, "Dropbox", "tbrush_notes")
	_, err := os.Stat(dir_path)
	if os.IsNotExist(err) {
		os.MkdirAll(dir_path, os.ModePerm)
	}

	dir_path_meta := filepath.Join(usr.HomeDir, ".toothbrush_meta")
	_, err = os.Stat(dir_path_meta)
	if os.IsNotExist(err) {
		os.MkdirAll(dir_path_meta, os.ModePerm)
	}

	log_path := filepath.Join(dir_path_meta, "out.log")
	f, _ := os.OpenFile(log_path, os.O_RDWR|os.O_CREATE|os.O_APPEND, 0666)
	defer f.Close()
	log.SetOutput(f)

	search_payload := SearchPayload{
		Query:         "",
		SelectedIndex: 0,
	}

	search_result := SearchResult{
		MatchedNames:    []string{},
		SelectedContent: "",
		SelectedName:    "",
	}

	app := tview.NewApplication()
	ui := UI{
		Table:    tview.NewTable(),
		TextView: tview.NewTextView(),
	}

	ui.Table.SetSelectable(true, true).SetBorder(true)

	post := func(endpoint string, payload interface{}, result interface{}) {
		post_to(host, port, endpoint, payload, result)
	}

	search := func() {
		defer func() {
			if r := recover(); r != nil {
				app.Stop()
			}
		}()

		search_for(&search_payload, &search_result, post, ui)

		app.Draw()
	}

	on_change := func(new_query string) {
		search_payload.Query = new_query
		go search()
	}
	input_field := tview.NewInputField().SetFieldWidth(100).SetChangedFunc(on_change)

	layout := tview.NewFlex().
			SetDirection(tview.FlexRow).
			AddItem(input_field, 1, 1, true).
			AddItem(ui.Table, 0, 1, false).
			AddItem(ui.TextView, 0, 1, false)


	app.SetInputCapture(func(event *tcell.EventKey) *tcell.EventKey {
		k := event.Key()

		if k == tcell.KeyEnter {
			open_note(
				"matrix flood_row_col",
				"/Users/jessealdridge/Dropbox/tbrush_notes",
			)
		}
		return event
	})
	if err := app.SetRoot(layout, true).Run(); err != nil {
		panic(err)
	}
}

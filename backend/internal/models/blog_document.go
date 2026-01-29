package models

import (
	"database/sql"
	"encoding/json"
	"time"

	"go-backend/internal/database"

	"github.com/google/uuid"
)

type BlogBrand string

const (
	BlogBrandOPEN   BlogBrand = "OPEN"
	BlogBrandZwitch BlogBrand = "Zwitch"
)

type BlogVersionStatus string

const (
	BlogVersionStatusDraft    BlogVersionStatus = "draft"
	BlogVersionStatusReviewed BlogVersionStatus = "reviewed"
	BlogVersionStatusApproved BlogVersionStatus = "approved"
)

type FeedbackScope string

const (
	FeedbackScopeGlobal  FeedbackScope = "global"
	FeedbackScopeSection FeedbackScope = "section"
)

type FeedbackTargetType string

const (
	FeedbackTargetOutline FeedbackTargetType = "outline"
	FeedbackTargetDraft   FeedbackTargetType = "draft"
)

// BlogDocument represents a blog document
type BlogDocument struct {
	ID             string     `json:"id"`
	Brand          BlogBrand  `json:"brand"`
	Topic          string     `json:"topic"`
	TargetAudience string     `json:"target_audience"`
	Intent         string     `json:"intent"`
	CreatedBy      *string    `json:"created_by,omitempty"`
	CreatedAt      time.Time  `json:"created_at"`
	UpdatedAt      time.Time  `json:"updated_at"`
}

// BlogOutlineVersion represents a version of a blog outline
type BlogOutlineVersion struct {
	ID          string             `json:"id"`
	DocumentID  string             `json:"document_id"`
	Version     int                `json:"version"`
	Structure   json.RawMessage   `json:"structure"` // {title, outline: [{heading, intent, subsections}]}
	Status      BlogVersionStatus  `json:"status"`
	CreatedAt   time.Time          `json:"created_at"`
}

// BlogDraftVersion represents a version of a blog draft
type BlogDraftVersion struct {
	ID                   string             `json:"id"`
	DocumentID           string             `json:"document_id"`
	OutlineVersionID     *string            `json:"outline_version_id,omitempty"`
	Version              int                `json:"version"`
	Content              string             `json:"content"`
	MetaDescription      *string            `json:"meta_description,omitempty"`
	WordCount            *int               `json:"word_count,omitempty"`
	EstimatedReadingTime *int               `json:"estimated_reading_time,omitempty"`
	Status               BlogVersionStatus   `json:"status"`
	CreatedAt            time.Time           `json:"created_at"`
}

// BlogFeedback represents feedback on an outline or draft
type BlogFeedback struct {
	ID              string             `json:"id"`
	DocumentID      string             `json:"document_id"`
	TargetType      FeedbackTargetType `json:"target_type"`
	TargetVersionID string             `json:"target_version_id"`
	Scope           FeedbackScope      `json:"scope"`
	TargetSectionID *string            `json:"target_section_id,omitempty"`
	Comment         string             `json:"comment"`
	CreatedBy       *string            `json:"created_by,omitempty"`
	CreatedAt       time.Time          `json:"created_at"`
}

// BlogDocumentRepository handles database operations for blog documents
type BlogDocumentRepository struct{}

func NewBlogDocumentRepository() *BlogDocumentRepository {
	return &BlogDocumentRepository{}
}

// Create creates a new blog document
func (r *BlogDocumentRepository) Create(brand BlogBrand, topic, targetAudience, intent, createdBy string) (*BlogDocument, error) {
	id := uuid.New().String()
	
	var createdByPtr *string
	if createdBy != "" {
		createdByPtr = &createdBy
	}

	query := `
		INSERT INTO blog_documents (id, brand, topic, target_audience, intent, created_by)
		VALUES ($1, $2, $3, $4, $5, $6)
		RETURNING id, brand, topic, target_audience, intent, created_by, created_at, updated_at
	`

	doc := &BlogDocument{}
	err := database.DB.QueryRow(query, id, brand, topic, targetAudience, intent, createdByPtr).Scan(
		&doc.ID, &doc.Brand, &doc.Topic, &doc.TargetAudience, &doc.Intent, &doc.CreatedBy, &doc.CreatedAt, &doc.UpdatedAt,
	)
	if err != nil {
		return nil, err
	}

	return doc, nil
}

// FindByID finds a blog document by ID
func (r *BlogDocumentRepository) FindByID(id string) (*BlogDocument, error) {
	query := `
		SELECT id, brand, topic, target_audience, intent, created_by, created_at, updated_at
		FROM blog_documents WHERE id = $1
	`

	doc := &BlogDocument{}
	var createdBy sql.NullString
	err := database.DB.QueryRow(query, id).Scan(
		&doc.ID, &doc.Brand, &doc.Topic, &doc.TargetAudience, &doc.Intent, &createdBy, &doc.CreatedAt, &doc.UpdatedAt,
	)
	if err == sql.ErrNoRows {
		return nil, nil
	}
	if err != nil {
		return nil, err
	}

	if createdBy.Valid {
		doc.CreatedBy = &createdBy.String
	}

	return doc, nil
}

// FindAll finds all blog documents
func (r *BlogDocumentRepository) FindAll(limit, offset int) ([]BlogDocument, int, error) {
	countQuery := `SELECT COUNT(*)::int FROM blog_documents`
	var total int
	err := database.DB.QueryRow(countQuery).Scan(&total)
	if err != nil {
		return nil, 0, err
	}

	query := `
		SELECT id, brand, topic, target_audience, intent, created_by, created_at, updated_at
		FROM blog_documents
		ORDER BY created_at DESC
		LIMIT $1 OFFSET $2
	`

	rows, err := database.DB.Query(query, limit, offset)
	if err != nil {
		return nil, 0, err
	}
	defer rows.Close()

	docs := []BlogDocument{}
	for rows.Next() {
		doc := BlogDocument{}
		var createdBy sql.NullString
		err := rows.Scan(
			&doc.ID, &doc.Brand, &doc.Topic, &doc.TargetAudience, &doc.Intent, &createdBy, &doc.CreatedAt, &doc.UpdatedAt,
		)
		if err != nil {
			return nil, 0, err
		}

		if createdBy.Valid {
			doc.CreatedBy = &createdBy.String
		}

		docs = append(docs, doc)
	}

	return docs, total, nil
}

// CreateOutlineVersion creates a new outline version
func (r *BlogDocumentRepository) CreateOutlineVersion(documentID string, version int, structure json.RawMessage, status BlogVersionStatus) (*BlogOutlineVersion, error) {
	id := uuid.New().String()

	query := `
		INSERT INTO blog_outline_versions (id, document_id, version, structure, status)
		VALUES ($1, $2, $3, $4, $5)
		RETURNING id, document_id, version, structure, status, created_at
	`

	outline := &BlogOutlineVersion{}
	err := database.DB.QueryRow(query, id, documentID, version, structure, status).Scan(
		&outline.ID, &outline.DocumentID, &outline.Version, &outline.Structure, &outline.Status, &outline.CreatedAt,
	)
	if err != nil {
		return nil, err
	}

	return outline, nil
}

// GetLatestOutlineVersion gets the latest outline version for a document
func (r *BlogDocumentRepository) GetLatestOutlineVersion(documentID string) (*BlogOutlineVersion, error) {
	query := `
		SELECT id, document_id, version, structure, status, created_at
		FROM blog_outline_versions
		WHERE document_id = $1
		ORDER BY version DESC
		LIMIT 1
	`

	outline := &BlogOutlineVersion{}
	err := database.DB.QueryRow(query, documentID).Scan(
		&outline.ID, &outline.DocumentID, &outline.Version, &outline.Structure, &outline.Status, &outline.CreatedAt,
	)
	if err == sql.ErrNoRows {
		return nil, nil
	}
	if err != nil {
		return nil, err
	}

	return outline, nil
}

// GetApprovedOutlineVersion gets the latest approved outline version
func (r *BlogDocumentRepository) GetApprovedOutlineVersion(documentID string) (*BlogOutlineVersion, error) {
	query := `
		SELECT id, document_id, version, structure, status, created_at
		FROM blog_outline_versions
		WHERE document_id = $1 AND status = 'approved'
		ORDER BY version DESC
		LIMIT 1
	`

	outline := &BlogOutlineVersion{}
	err := database.DB.QueryRow(query, documentID).Scan(
		&outline.ID, &outline.DocumentID, &outline.Version, &outline.Structure, &outline.Status, &outline.CreatedAt,
	)
	if err == sql.ErrNoRows {
		return nil, nil
	}
	if err != nil {
		return nil, err
	}

	return outline, nil
}

// UpdateOutlineVersionStatus updates the status of an outline version
func (r *BlogDocumentRepository) UpdateOutlineVersionStatus(versionID string, status BlogVersionStatus) error {
	query := `UPDATE blog_outline_versions SET status = $1 WHERE id = $2`
	_, err := database.DB.Exec(query, status, versionID)
	return err
}

// UpdateOutlineVersionStructure updates the structure of an outline version
func (r *BlogDocumentRepository) UpdateOutlineVersionStructure(versionID string, structure json.RawMessage) error {
	query := `UPDATE blog_outline_versions SET structure = $1 WHERE id = $2`
	_, err := database.DB.Exec(query, structure, versionID)
	return err
}

// CreateDraftVersion creates a new draft version
func (r *BlogDocumentRepository) CreateDraftVersion(documentID string, outlineVersionID *string, version int, content, metaDescription string, wordCount, readingTime *int, status BlogVersionStatus) (*BlogDraftVersion, error) {
	id := uuid.New().String()

	var metaDescPtr *string
	if metaDescription != "" {
		metaDescPtr = &metaDescription
	}

	query := `
		INSERT INTO blog_draft_versions (id, document_id, outline_version_id, version, content, meta_description, word_count, estimated_reading_time, status)
		VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
		RETURNING id, document_id, outline_version_id, version, content, meta_description, word_count, estimated_reading_time, status, created_at
	`

	draft := &BlogDraftVersion{}
	var outlineID sql.NullString
	var metaDesc sql.NullString
	err := database.DB.QueryRow(query, id, documentID, outlineVersionID, version, content, metaDescPtr, wordCount, readingTime, status).Scan(
		&draft.ID, &draft.DocumentID, &outlineID, &draft.Version, &draft.Content, &metaDesc, &draft.WordCount, &draft.EstimatedReadingTime, &draft.Status, &draft.CreatedAt,
	)
	if err != nil {
		return nil, err
	}

	if outlineID.Valid {
		draft.OutlineVersionID = &outlineID.String
	}
	if metaDesc.Valid {
		draft.MetaDescription = &metaDesc.String
	}

	return draft, nil
}

// GetLatestDraftVersion gets the latest draft version for a document
func (r *BlogDocumentRepository) GetLatestDraftVersion(documentID string) (*BlogDraftVersion, error) {
	query := `
		SELECT id, document_id, outline_version_id, version, content, meta_description, word_count, estimated_reading_time, status, created_at
		FROM blog_draft_versions
		WHERE document_id = $1
		ORDER BY version DESC
		LIMIT 1
	`

	draft := &BlogDraftVersion{}
	var outlineID sql.NullString
	var metaDesc sql.NullString
	err := database.DB.QueryRow(query, documentID).Scan(
		&draft.ID, &draft.DocumentID, &outlineID, &draft.Version, &draft.Content, &metaDesc, &draft.WordCount, &draft.EstimatedReadingTime, &draft.Status, &draft.CreatedAt,
	)
	if err == sql.ErrNoRows {
		return nil, nil
	}
	if err != nil {
		return nil, err
	}

	if outlineID.Valid {
		draft.OutlineVersionID = &outlineID.String
	}
	if metaDesc.Valid {
		draft.MetaDescription = &metaDesc.String
	}

	return draft, nil
}

// AddFeedback adds feedback to an outline or draft
func (r *BlogDocumentRepository) AddFeedback(documentID string, targetType FeedbackTargetType, targetVersionID string, scope FeedbackScope, targetSectionID *string, comment, createdBy string) (*BlogFeedback, error) {
	id := uuid.New().String()

	var createdByPtr *string
	if createdBy != "" {
		createdByPtr = &createdBy
	}

	query := `
		INSERT INTO blog_feedback (id, document_id, target_type, target_version_id, scope, target_section_id, comment, created_by)
		VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
		RETURNING id, document_id, target_type, target_version_id, scope, target_section_id, comment, created_by, created_at
	`

	feedback := &BlogFeedback{}
	var sectionID sql.NullString
	var createdByNull sql.NullString
	err := database.DB.QueryRow(query, id, documentID, targetType, targetVersionID, scope, targetSectionID, comment, createdByPtr).Scan(
		&feedback.ID, &feedback.DocumentID, &feedback.TargetType, &feedback.TargetVersionID, &feedback.Scope, &sectionID, &feedback.Comment, &createdByNull, &feedback.CreatedAt,
	)
	if err != nil {
		return nil, err
	}

	if sectionID.Valid {
		feedback.TargetSectionID = &sectionID.String
	}
	if createdByNull.Valid {
		feedback.CreatedBy = &createdByNull.String
	}

	return feedback, nil
}

// GetFeedbackForVersion gets all feedback for a specific version
func (r *BlogDocumentRepository) GetFeedbackForVersion(targetVersionID string) ([]BlogFeedback, error) {
	query := `
		SELECT id, document_id, target_type, target_version_id, scope, target_section_id, comment, created_by, created_at
		FROM blog_feedback
		WHERE target_version_id = $1
		ORDER BY created_at ASC
	`

	rows, err := database.DB.Query(query, targetVersionID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	feedbacks := []BlogFeedback{}
	for rows.Next() {
		feedback := BlogFeedback{}
		var sectionID sql.NullString
		var createdBy sql.NullString
		err := rows.Scan(
			&feedback.ID, &feedback.DocumentID, &feedback.TargetType, &feedback.TargetVersionID, &feedback.Scope, &sectionID, &feedback.Comment, &createdBy, &feedback.CreatedAt,
		)
		if err != nil {
			return nil, err
		}

		if sectionID.Valid {
			feedback.TargetSectionID = &sectionID.String
		}
		if createdBy.Valid {
			feedback.CreatedBy = &createdBy.String
		}

		feedbacks = append(feedbacks, feedback)
	}

	return feedbacks, nil
}

// GetNextOutlineVersion gets the next version number for an outline
func (r *BlogDocumentRepository) GetNextOutlineVersion(documentID string) (int, error) {
	query := `
		SELECT COALESCE(MAX(version), 0) + 1
		FROM blog_outline_versions
		WHERE document_id = $1
	`

	var version int
	err := database.DB.QueryRow(query, documentID).Scan(&version)
	if err != nil {
		return 1, err
	}

	return version, nil
}

// GetNextDraftVersion gets the next version number for a draft
func (r *BlogDocumentRepository) GetNextDraftVersion(documentID string) (int, error) {
	query := `
		SELECT COALESCE(MAX(version), 0) + 1
		FROM blog_draft_versions
		WHERE document_id = $1
	`

	var version int
	err := database.DB.QueryRow(query, documentID).Scan(&version)
	if err != nil {
		return 1, err
	}

	return version, nil
}
